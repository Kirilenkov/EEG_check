import numpy as np
from pathlib import Path

import analyze_eeg_mne as mod


def test_format_seconds():
    assert mod.format_seconds(None) == "unknown"
    assert mod.format_seconds(0) == "00:00:00.000"
    assert mod.format_seconds(1.234) == "00:00:01.234"
    assert mod.format_seconds(3661.5) == "01:01:01.500"


def test_as_float_various():
    assert mod.as_float(5) == 5.0
    assert mod.as_float(3.14) == 3.14
    assert mod.as_float(np.array([7])) == 7.0
    assert mod.as_float(np.array([[2.5]])) == 2.5
    assert mod.as_float(np.float64(1.25)) == 1.25
    assert mod.as_float([42]) == 42.0
    assert mod.as_float([]) is None


def test_to_str_various():
    assert mod.to_str("abc") == "abc"
    assert mod.to_str(b"xyz") == "xyz"
    arr = np.array(["A", "B"])  # numpy array of strings
    s = mod.to_str(arr)
    assert isinstance(s, str)
    assert "A" in s and "B" in s


def test_to_ndarray_identity_and_object_unpack():
    x = np.array([[1, 2], [3, 4]])
    assert isinstance(mod.to_ndarray(x), np.ndarray)
    obj_arr = np.array([np.array([1, 2, 3])], dtype=object)
    y = mod.to_ndarray(obj_arr)
    assert isinstance(y, np.ndarray)


def test_get_field_with_npvoid():
    dt = np.dtype([("a", "f8"), ("b", "i4")])
    rec = np.array((3.5, 7), dtype=dt)[()]  # produce np.void
    assert mod.get_field(rec, "a") == 3.5
    assert mod.get_field(rec, "b") == 7


def test_analyze_epochs_dummy_counts():
    class Dummy:
        def __init__(self):
            self.info = {"sfreq": 100.0}
            self.n_times = 200
            self.ch_names = ["Cz", "Pz"]
            self.event_id = {"A": 1, "B": 2}
            self.events = np.array([[0, 0, 1], [0, 0, 2], [0, 0, 1]], dtype=int)

        def __len__(self):
            return 3

    d = Dummy()
    res = mod.analyze_epochs(d)
    assert res["type"] == "epochs"
    assert res["n_epochs"] == 3
    assert res["sfreq"] == 100.0
    assert res["labels_counts"]["A"] == 2
    assert res["labels_counts"]["B"] == 1


def test_analyze_mat_monkeypatch(monkeypatch):
    # Build synthetic MATLAB-like dict
    def fake_loadmat(_):
        data = np.zeros((2, 100, 5))  # 2 ch, 100 samples per epoch, 5 epochs
        eeg = {
            "data": data,
            "srate": 200.0,
            "event": [{"type": "X"}, {"type": "Y"}, {"type": "X"}],
        }
        return {"EEG": eeg}

    monkeypatch.setattr(mod, "loadmat_safely", fake_loadmat)
    res = mod.analyze_mat(Path("dummy.mat"))
    assert res["type"] == "mat"
    assert res["n_epochs"] == 5
    assert res["sfreq"] == 200.0
    assert res["samples_per_epoch"] == 100
    assert res["labels_counts"]["X"] == 2
    assert res["labels_counts"]["Y"] == 1
