# Документация к скрипту `analyze_eeg_mne.py`

Подробное описание назначения скрипта, архитектуры, функций и ключевых переменных.

## Назначение
Скрипт анализирует EEG-файлы в указанной папке (по умолчанию `./data`) и для каждого файла извлекает:
- частоту дискретизации (`sfreq`),
- количество каналов (`n_channels`),
- длительность записи/эпох в секундах (`duration_sec`),
- число эпох (`n_epochs`),
- наличие и распределение меток/событий (`labels_counts`).

Выводит сводку в консоль, сохраняет результаты в CSV и при наличии matplotlib
строит графики (распределение меток, длительности и количества эпох по файлам).

Поддерживаемые форматы: EDF, BDF, FIF, BrainVision (.vhdr/.eeg), CNT, EEGLAB (.set), MATLAB (.mat).

## Архитектура и поток выполнения
1. `main()` разбирает аргументы `--data-dir`, `--recursive`, `--output-dir`, `--output-csv-prefix`, `--no-plots`.
2. `gather_files()` собирает список поддерживаемых файлов в папке; при `--recursive` обходит подкаталоги.
3. Для каждого файла вызывается `analyze_file()`:
   - Определяется расширение и выбирается путь чтения.
   - Для MNE-поддерживаемых форматов вызывается `read_with_mne()` с возвратом `("raw"|"epochs", obj)`.
   - Для `.mat` — вызывается `analyze_mat()`.
4. Полученный объект обрабатывается соответствующей функцией:
   - `analyze_raw()` — для непрерывных записей (`Raw`).
   - `analyze_epochs()` — для разметки эпох (`Epochs`).
5. Накапливаются общие итоги: суммарная длительность, число эпох, распределение меток.
6. Печать детальной сводки по файлам и общих итогов.
7. Сохранение CSV-отчетов (`*_files.csv`, `*_labels.csv`).
8. Построение и сохранение графиков (`*_labels.png`, `*_durations.png`, `*_epochs.png`), если не задан `--no-plots` и доступен matplotlib.

## Функции

### `format_seconds(total_seconds: float) -> str`
Преобразует число секунд в строку формата `HH:MM:SS.mmm`. Если вход `None` — возвращает `"unknown"`.

### `as_float(x)`
Безопасно приводит значение к `float`. Поддерживает: числа Python, numpy-скаляры, массивы/контейнеры с 1 элементом. При невозможности — `None`.

### `get_field(obj, key)`
Извлекает поле/атрибут из объекта/словаря/структуры MATLAB (`np.void`). Если поле есть и это одиночный `ndarray`, разворачивает в скаляр. Иначе возвращает значение как есть. При отсутствии — `None`.

### `to_ndarray(x)`
Пробует превратить вход в `numpy.ndarray`. Для объектных массивов с одним элементом делает попытку распаковать `item()`. При неудаче — `None`.

### `to_str(x)`
Нормализует произвольное значение к `str` (строки, байты, numpy‑массивы строк/скаляры). Используется для унификации меток событий.

### `analyze_raw(raw)`
Анализирует объект `mne.io.Raw`:
- `sfreq` — из `raw.info['sfreq']`.
- `duration_sec` — `raw.n_times / sfreq`.
- `n_channels` — длина `raw.ch_names`.
- Метки: сначала `raw.annotations.description`, иначе `mne.find_events()` по стим‑каналу (`stim_channel="auto"`).
- `n_epochs` всегда 0 (для непрерывной записи).
Возвращает словарь метрик.

### `analyze_epochs(epochs)`
Анализирует `mne.Epochs`:
- `sfreq` — из `epochs.info['sfreq']`.
- `n_epochs` — `len(epochs)`.
- `epoch_dur` — `epochs.n_times / sfreq`.
- `duration_sec` — `n_epochs * epoch_dur`.
- Метки: через `epochs.events[:, 2]` с маппингом из `epochs.event_id`.
Возвращает словарь метрик.

### `read_with_mne(path: Path)`
Пробует прочитать файл через MNE, возвращает кортеж `(kind, obj)`:
- `kind == "raw"` для EDF/BDF/BrainVision/CNT/FIF (Raw),
- `kind == "epochs"` для FIF (Epochs) или EEGLAB (`.set`, через `mne.read_epochs_eeglab()`),
- при ошибках чтения — `(None, None)`.

Особенность для BrainVision: если найден `.eeg`, пытается использовать соседний `.vhdr`.

### `loadmat_safely(f: str)`
Загружает `.mat` с `scipy.io.loadmat`. Сначала пробует `simplify_cells=True`, затем fallback на старые параметры. Возвращает `dict` или `None`.

### `analyze_mat(path: Path)`
Эвристический анализ `.mat`:
- Ищет структуру `EEG` с полями `data/x`, `srate/fs/Fs` и `event`.
- Если нет — ищет данные в `data/X/signals/x` и частоту в `fs/Fs/srate/sampling_rate/sr`.
- Если данные `2D`: `(n_channels, n_times)` — `n_epochs = 0`, длительность `n_times / sfreq`.
- Если `3D`: `(n_channels, n_times, n_epochs)` — длительность `(n_times * n_epochs) / sfreq`.
- Метки: `EEG.event.type` или общие поля (`labels`, `y`, `events`, `trialinfo`, `trials_labels`).
Возвращает словарь метрик.

### `analyze_file(path: Path)`
Определяет по расширению, какой путь анализа применить: через MNE (`read_with_mne`) или через MATLAB‑парсер (`analyze_mat`). Дополняет результат полями `format`, `file`, `path`.

### `gather_files(data_dir: Path, recursive: bool = False)`
Возвращает список файлов с поддерживаемыми расширениями в папке. Если `recursive=True`,
рекурсивно обходит подкаталоги с помощью `Path.rglob("*")`.

### `ensure_output_dir(path: Path)`
Создает выходную папку при необходимости (`mkdir(parents=True, exist_ok=True)`).

### `save_csv_summaries(results, total_counts: Counter, output_dir: Path, prefix: str)`
Сохраняет два CSV:
- `prefix_files.csv` — сводка по файлам: `file, format, type, sfreq, n_channels, duration_sec, duration_str, n_epochs, has_labels, labels_total`.
- `prefix_labels.csv` — совокупное распределение меток: `label, count`.
Возвращает пути к CSV-файлам.

### `plot_summaries(results, total_counts: Counter, output_dir: Path, prefix: str)`
Строит графики и сохраняет PNG:
- `prefix_labels.png` — горизонтальная диаграмма топ‑30 меток.
- `prefix_durations.png` — длительности (сек) по файлам.
- `prefix_epochs.png` — количество эпох по файлам.
Использует seaborn при наличии, иначе — matplotlib. Возвращает список путей к изображениям.

### `main()`
Точка входа: парсинг аргументов, запуск анализа, печать сводки, сохранение CSV и графиков.

## Ключевые переменные и структуры
- `results: list[dict]` — метрики по каждому файлу.
- `total_duration: float` — суммарная длительность по всем файлам (секунды).
- `total_epochs: int` — суммарное число эпох.
- `total_counts: Counter[str, int]` — сводное распределение меток.
- В элементах `results` для каждого файла:
  - `type: str` — тип обработанного объекта (`raw`/`epochs`/`mat`/`unknown`/`error`).
  - `sfreq: float | None`
  - `n_channels: int | None`
  - `duration_sec: float | None`
  - `n_epochs: int`
  - `labels_counts: dict[str, int]`
  - `has_labels: bool`
  - `format: str` — расширение файла.
  - `file: str` — имя файла.
  - `path: str` — полный путь.
  - `error: str` — при ошибке чтения.

## Ограничения и замечания
- Для `.set` сначала пробуется чтение `Epochs`, при неудаче — `Raw`.
- В MATLAB‑файлах структура может сильно отличаться; реализованы популярные эвристики, но нестандартные форматы потребуют адаптации.
- Для экономии памяти в MNE чтение происходит с `preload=False`.
- Построение графиков требует установленного `matplotlib` (и опционально `seaborn`).

## Расширение и доработка
- Экспорт в Excel (`.xlsx`).
- Интерактивные HTML‑графики (Plotly/Bokeh).
- Фильтры по маске имен файлов и по длительности.

## Примеры запуска
PowerShell:
```powershell
python analyze_eeg_mne.py --data-dir data --recursive --output-dir out --output-csv-prefix eeg
```

Bash:
```bash
python3 analyze_eeg_mne.py --data-dir data --recursive --output-dir out --output-csv-prefix eeg
```
