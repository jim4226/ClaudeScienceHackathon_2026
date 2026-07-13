# Example ECG attribution

The example records bundled here are **real 12-lead ECGs from PTB-XL**, included
under the dataset's CC-BY 4.0 license with attribution.

- **Dataset:** PTB-XL, a large publicly available electrocardiography dataset (v1.0.3).
- **Source:** PhysioNet — https://physionet.org/content/ptb-xl/1.0.3/
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Citation:** Wagner, P., Strodthoff, N., Bousseljot, R.-D., Kreiseler, D.,
  Lunze, F. I., Samek, W., & Schaeffter, T. (2020). PTB-XL, a large publicly
  available electrocardiography dataset. *Scientific Data*, 7, 154.
  Also cite PhysioNet (Goldberger et al., *Circulation* 2000).

| File | PTB-XL ecg_id | Age | Sex | Label |
|---|---|---|---|---|
| `00420_hr` | 420 | 22 | M | sinus rhythm, normal ECG |
| `00233_hr` | 233 | 52 | M | sinus rhythm, normal ECG |
| `00176_hr` | 176 | 77 | F | sinus rhythm, normal ECG |

Each record is the 500 Hz, 10-second, 12-lead signal (`.hea` + `.dat`) exactly as
distributed by PhysioNet. No modification was made.
