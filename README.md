# Анализ ЭЭГ в папке `data` (MNE)

Скрипт `analyze_eeg_mne.py` сканирует папку с данными и для каждого файла определяет:
- частоту дискретизации,
- количество каналов,
- длительность записи/эпох,
- наличие и распределение меток (аннотаций/событий),
а затем печатает сводку, сохраняет CSV-отчеты, формирует Excel по эпохам и при наличии matplotlib строит графики.

Поддерживаемые форматы: EDF, BDF, FIF, BrainVision (.vhdr/.eeg), CNT, EEGLAB (.set), MATLAB (.mat).

## Требования
- Python 3.9+
- Пакеты: mne, scipy, numpy, matplotlib, seaborn, openpyxl (для Excel)

Установить зависимости (PowerShell):
```powershell
python -m pip install -r requirements.txt
```
Установить зависимости (Bash):
```bash
python3 -m pip install -r requirements.txt
```

Опционально (виртуальное окружение, PowerShell):
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Опционально (виртуальное окружение, Bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Структура проекта
```
windsurf-project/
├─ analyze_eeg_mne.py
├─ requirements.txt
├─ data/
│  └─ <ваши EEG файлы>
└─ out/                 # если указать --output-dir out
   ├─ eeg_analysis_files.csv
   ├─ eeg_analysis_labels.csv
   ├─ eeg_analysis_labels.png
   ├─ eeg_analysis_durations.png
   └─ eeg_analysis_epochs.png
```

## Быстрый старт
Запуск без флагов (используются значения по умолчанию: `data` и `.`):

PowerShell:
```powershell
python analyze_eeg_mne.py
```

Bash:
```bash
python3 analyze_eeg_mne.py
```

Позиционные аргументы (также без флагов):

PowerShell:
```powershell
python analyze_eeg_mne.py data out
```

Bash:
```bash
python3 analyze_eeg_mne.py data out
```

Запустить анализ с рекурсивным обходом и сохранением результатов в папку `out`:

PowerShell:
```powershell
python analyze_eeg_mne.py --data-dir data --recursive --output-dir out --output-csv-prefix eeg_analysis
```

Bash:
```bash
python3 analyze_eeg_mne.py --data-dir data --recursive --output-dir out --output-csv-prefix eeg_analysis
```

Параметры:
- Позиционные: `pos_data_dir` (папка с данными), `pos_output_dir` (папка вывода). Если не указаны — используются `data` и `.`.
- `--data-dir` — папка с данными.
- `--recursive` — рекурсивный обход подкаталогов.
- `--output-dir` — папка для сохранения CSV и графиков (по умолчанию текущая `.`).
- `--output-csv-prefix` — префикс имен выходных файлов (например, `eeg_analysis`).
- `--no-plots` — отключить построение графиков.

Прецедентность значений путей:
- сначала учитываются флаги `--data-dir`/`--output-dir` (если заданы),
- затем позиционные аргументы,
- затем значения по умолчанию (`data`, `.`).

## Вывод в консоль
Для каждого файла:
- имя, формат и тип объекта (raw/epochs/mat),
- `fs` (частота дискретизации),
- число каналов,
- длительность (HH:MM:SS.mmm),
- число эпох,
- количество обнаруженных меток.

Итоги по всей папке:
- суммарная длительность (в человекочитаемом виде и секундах),
- суммарное число эпох,
- сводное распределение меток.

## CSV‑отчеты
Скрипт сохраняет два CSV‑файла:

- `*_files.csv` — сводка по каждому файлу. Столбцы:
  - `file`, `format`, `type`, `sfreq`, `n_channels`, `duration_sec`, `duration_str`, `n_epochs`, `has_labels`, `labels_total`.

- `*_labels.csv` — совокупное распределение меток по всей папке. Столбцы:
  - `label`, `count`.

## Excel по эпохам
Скрипт создает файл `*_epochs.xlsx` (по одному листу на файл Epochs), где для каждой эпохи указано:

- `file` — имя исходного файла
- `epoch_index` — номер эпохи (1..N)
- `samples_per_epoch` — длительность эпохи в сэмплах
- `seconds_per_epoch` — длительность эпохи в секундах
- `label_code` — код события эпохи
- `label_name` — имя метки (по словарю `event_id`), если доступно

## Особенности и примечания
- Для `Raw`-файлов метки берутся из `raw.annotations` или через `mne.find_events()` из стим‑канала.
- Для `Epochs` метки определяются по `epochs.events` и словарю `event_id`.
- Для `.mat` применяются эвристики: ищутся поля `EEG.data`, `EEG.srate`, `EEG.event.type`, а также общие ключи `data/X/signals/x` и `fs/Fs/srate`.
- Для BrainVision (`.eeg`) используется парный `.vhdr` рядом с файлом.
- Скрипт не использует `preload=True`, чтобы экономить память.
- Рекурсивный обход доступен через флаг `--recursive`.
- Графики сохраняются, если установлен `matplotlib` (и опционально `seaborn`).

## Возможные расширения
- Экспорт в Excel (`.xlsx`).
- Интерактивные HTML‑графики (Plotly/Bokeh).

## Устранение неполадок
- Убедитесь, что формат соответствует поддерживаемым расширениям.
- Для `.set` (EEGLAB) при невозможности прочитать Epochs, скрипт пытается прочитать Raw.
- Для необычных `.mat` структур добавьте примеры ключей — расширим парсер.

## Лицензия
Свободно используйте и модифицируйте в рамках вашего проекта.
