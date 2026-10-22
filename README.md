# Hướng Dẫn Cài Đặt Môi Trường & Thiết Lập Thông Số Chạy Notebook
### Dự Báo Nhu Cầu Tiêu Thụ Điện (Electricity Demand Forecasting)

Tài liệu này hướng dẫn chi tiết quy trình thiết lập môi trường, cấu hình đường dẫn dữ liệu, điều chỉnh các siêu tham số và chạy hai notebook trong dự án:
1. **`SARIMAX.ipynb`**: Phương pháp thống kê chuỗi thời gian cổ điển (ARIMA, SARIMA, SARIMAX kết hợp biến ngoại sinh thời tiết và Grid Search).
2. **`NEW_models.ipynb`**: Phương pháp học sâu hiện đại (LSTM và Transformer Encoder với Attention Pooling, tiền xử lý dữ liệu qua DuckDB).

---

## 1. Cấu Trúc Thư Mục Dự Án

Cấu trúc thư mục khuyến nghị để hai notebook hoạt động chính xác:

```text
├── data/                                 # Thư mục chứa dữ liệu thô (.parquet)
│   ├── demand.parquet                    # Dữ liệu tiêu thụ điện theo thời gian
│   ├── metadata.parquet                  # Thông tin metadata các công tơ đo
│   └── weather.parquet                   # Dữ liệu thời tiết theo thời gian
│
└── electricity-demand-forecasting/       # Thư mục code hiện tại
    ├── README.md                         # File hướng dẫn này
    ├── requirements.txt                  # Danh sách thư viện phụ thuộc
    ├── SARIMAX.ipynb                     # Notebook mô hình chuỗi thời gian thống kê
    ├── NEW_models.ipynb                  # Notebook mô hình Deep Learning (LSTM & Transformer)
    ├── checkpoints_lstm/                 # Checkpoints mô hình LSTM đã huấn luyện
    │   ├── best.pt                       # Trọng số validation loss thấp nhất
    │   └── last.pt                       # Trọng số tại epoch cuối
    └── checkpoints_transformer/          # Checkpoints mô hình Transformer
        ├── best.pt
        └── last.pt
```

> [!IMPORTANT]
> **Lưu ý về đường dẫn dữ liệu:**
> Trong cả hai file notebook gốc, biến đường dẫn dữ liệu mặc định là `../../data`. Nếu bạn đặt thư mục `data` nằm ngang hàng với thư mục `electricity-demand-forecasting` (tức `../data`), hãy đổi biến đường dẫn trong notebook thành `'../data'` (xem chi tiết ở mục 4 và 5).

---

## 2. Yêu Cầu Hệ Thống & Cài Đặt Môi Trường

### 2.1. Yêu cầu hệ thống
- **Hệ điều hành**: Linux / macOS / Windows 10/11 (khuyến nghị WSL2 nếu dùng Windows).
- **Python**: Phiên bản khuyến nghị `3.10`, `3.11` hoặc `3.12` (hỗ trợ cả `3.13`).
- **Phần cứng**:
  - Tối thiểu 8 GB RAM (khuyến nghị 16 GB để nạp và xử lý tập dữ liệu Parquet gần 300 MB).
  - Có GPU NVIDIA hỗ trợ CUDA là lợi thế lớn khi huấn luyện mô hình trong `NEW_models.ipynb` (nếu không có GPU, code sẽ tự động chạy trên CPU).

---

### 2.2. Cách 1: Cài đặt bằng Anaconda / Miniconda (Khuyến nghị)

Sử dụng Conda giúp quản lý môi trường độc lập, tránh xung đột các thư viện C/Cython như `statsmodels`, `pmdarima` và `torch`.

#### Bước 1: Tạo và kích hoạt môi trường Conda
```bash
# Tạo môi trường mới với Python 3.11
conda create -n elec_forecast python=3.11 -y

# Kích hoạt môi trường
conda activate elec_forecast
```

#### Bước 2: Cài đặt PyTorch
- **Nếu máy có GPU NVIDIA (CUDA):**
  ```bash
  # Cài đặt PyTorch với CUDA 12.1 hoặc 11.8 (tùy driver card đồ họa)
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
  ```
- **Nếu máy chỉ dùng CPU:**
  ```bash
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  ```

#### Bước 3: Cài đặt các thư viện phụ thuộc
```bash
cd /duong/dan/toi/electricity-demand-forecasting
pip install -r requirements.txt
```

#### Bước 4: Đăng ký Kernel vào Jupyter
```bash
python -m ipykernel install --user --name elec_forecast --display-name "Python (elec_forecast)"
```

---

### 2.3. Cách 2: Cài đặt bằng Python Virtualenv (`venv`) chuẩn

Nếu không sử dụng Conda, bạn có thể tạo môi trường ảo Python thông thường:

```bash
# Di chuyển vào thư mục dự án
cd /duong/dan/toi/electricity-demand-forecasting

# Tạo virtualenv
python3 -m venv venv

# Kích hoạt môi trường ảo:
# Trên Linux / macOS:
source venv/bin/activate
# Trên Windows (Command Prompt / PowerShell):
# venv\Scripts\activate

# Nâng cấp pip
pip install --upgrade pip

# Cài đặt PyTorch (xem mục 2.2 nếu muốn cài bản CUDA riêng)
pip install torch

# Cài đặt toàn bộ danh sách thư viện
pip install -r requirements.txt

# Đăng ký kernel cho Jupyter
python -m ipykernel install --user --name venv_elec --display-name "Python (venv_elec)"
```

---

### 2.4. Khởi chạy Jupyter Notebook / JupyterLab

Sau khi cài đặt xong môi trường, khởi động máy chủ Jupyter:

```bash
jupyter lab
# hoặc
jupyter notebook
```

Khi mở từng file notebook (`.ipynb`), tại góc trên bên phải giao diện Jupyter, chọn **Kernel** tương ứng (`Python (elec_forecast)` hoặc kernel môi trường vừa tạo).

---

## 3. Danh Sách Thư Viện Chính (`requirements.txt`)

| Thư viện | Phiên bản | Vai trò chính |
| :--- | :--- | :--- |
| `torch` | $\ge 2.0.0$ | Huấn luyện mô hình Deep Learning (LSTM, Transformer) |
| `duckdb` | $\ge 0.9.0$ | Truy vấn và tổng hợp nhanh dữ liệu Parquet lớn |
| `statsmodels` | $\ge 0.14.0$ | Mô hình hóa chuỗi thời gian ARIMA, SARIMAX, kiểm định ADF, ACF/PACF |
| `pmdarima` | $\ge 2.0.0$ | Tự động dò tìm bậc mô hình `auto_arima` |
| `scikit-learn` | $\ge 1.2.0$ | Chuẩn hóa dữ liệu (`StandardScaler`), tính hàm độ đo lỗi (RMSE, MAE, MAPE) |
| `pandas` | $\ge 2.0.0$ | Xử lý dữ liệu bảng, thao tác thời gian (resampling, datetime) |
| `numpy` | $\ge 1.24.0$ | Tính toán ma trận và đại số số học |
| `scipy` | $\ge 1.10.0$ | Phân tích phân phối sai số, Q-Q plot, Gaussian Log-Likelihood |
| `matplotlib` & `seaborn` | $\ge 3.7.0$ | Vẽ biểu đồ chuỗi thời gian, ma trận tương quan, so sánh dự báo |
| `pyarrow` | $\ge 12.0.0$ | Đọc/ghi định dạng dữ liệu cột Apache Parquet |
| `GPy` | $\ge 1.10.0$ | Thư viện Gaussian Process (được import trong SARIMAX) |

> [!NOTE]
> `GPy` chỉ được import ở cell đầu tiên của `SARIMAX.ipynb` mà không dùng ở các bước phân tích chính sau đó. Nếu quá trình cài đặt `GPy` gặp lỗi về trình biên dịch C, bạn có thể comment dòng `# import GPy` trong Cell 1 của `SARIMAX.ipynb` mà không ảnh hưởng tới kết quả chạy.

---

## 4. Hướng Dẫn Chi Tiết & Thiết Lập Thông Số Cho `SARIMAX.ipynb`

Notebook này tập trung phân tích chuỗi thời gian thống kê cổ điển, kiểm tra tính dừng (Augmented Dickey-Fuller Test), tính chu kỳ (Fourier / ACF / PACF), và thử nghiệm các mô hình ARIMA $\rightarrow$ SARIMA $\rightarrow$ SARIMAX.

### 4.1. Thiết lập đường dẫn dữ liệu (Cell 2)
Mặc định trong notebook:
```python
parquet_directory = '../../data'  # <-- Cần sửa lại cho đúng vị trí thực tế
metadata_file = f'{parquet_directory}/metadata.parquet'
demand_file = f'{parquet_directory}/demand.parquet'
weather_file = f'{parquet_directory}/weather.parquet'
```
**Chỉnh sửa phù hợp:**
- Nếu thư mục `data` nằm cùng cấp với `electricity-demand-forecasting`: Đổi thành:
  ```python
  parquet_directory = '../data'
  ```
- Hoặc sử dụng đường dẫn tuyệt đối:
  ```python
  parquet_directory = '/home/jiooum/Downloads/data'
  ```

---

### 4.2. Các thông số tiền xử lý dữ liệu quan trọng
- **Lọc tập dữ liệu (Cell 5, Cell 7)**:
  - Chọn tập `Electricity Load Diagrams`: `metadata['dataset'] == "Electricity Load Diagrams"`.
  - Giới hạn ngày trực quan hóa số lượng đồng hồ đo: $\le$ `2025-01-01`.
- **Lọc mốc thời gian 15 phút (Cell 11)**:
  - Tạo lưới 15 phút từ `00:00` đến `23:59` để loại bỏ các timestamp không chuẩn.
  - Tính trung bình mức tiêu thụ theo từng công tơ theo ngày:
    `daily_demand = london_demand.groupby('date')['y'].mean().reset_index()`
- **Phân chia Train / Test (Cell 13)**:
  - `split_date_daily = "2024-01-01"`
  - **Tập Train**: Các ngày trước `2024-01-01` (dữ liệu các năm trước đó).
  - **Tập Test**: Các ngày từ `2024-01-01` đến hết năm 2024.
- **Xử lý các ngày bị khuyết trong tập Test (Cell 47)**:
  - Thuật toán kiểm tra các ngày còn thiếu trong tập test so với chuỗi ngày liên tục của dữ liệu thời tiết và nội suy tuyến tính bằng trung bình của ngày hôm trước và ngày hôm sau.
  > [!WARNING]
  > **Chú ý Cell 47**: Cell này thực hiện `pd.concat` nối trực tiếp các ngày thiếu vào `test_data_daily`. Nếu bạn chạy Cell 47 nhiều lần liên tiếp trong cùng một phiên kernel, các dòng này sẽ bị lặp lại. Nếu cần chạy lại, hãy restart kernel hoặc chạy lại từ Cell 13.

---

### 4.3. Thiết lập thông số mô hình

| Bước / Cell | Mô hình | Các thông số chính | Ý nghĩa & Khuyến nghị |
| :--- | :--- | :--- | :--- |
| **Cell 33** | `auto_arima` (ARIMA phi mùa) | `start_p=0, max_p=3`, `start_q=0, max_q=5`, `seasonal=False`, `stepwise=True`, `n_jobs=-1` | Tìm bậc ARIMA tốt nhất không xét mùa. Dò ra mô hình ARIMA(3, 1, 4). |
| **Cell 37** | `ARIMA(3, 1, 4)` | `order=(3, 1, 4)` | Khớp mô hình với `statsmodels` để lấy giá trị Log-Likelihood chính xác. |
| **Cell 39** | `auto_arima` (SARIMA có mùa) | `start_p=0, max_p=2`, `start_q=0, max_q=2`, `start_P=0, max_P=5`, `start_Q=0, max_Q=5`, `m=7` | `m=7` phản ánh tính chu kỳ theo tuần (7 ngày). Dò ra SARIMA(1, 1, 2)(2, 0, 2, 7). |
| **Cell 40** | `SARIMAX` | `order=(1, 1, 2)`, `seasonal_order=(2, 0, 2, 7)`, `trend='c'` | Khớp mô hình SARIMA cơ sở. |
| **Cell 51** | Lựa chọn biến thời tiết | `filters`: dictionary chứa 4 tập biến (a, b, c, d) | Đánh giá tác động của các biến ngoại sinh thời tiết. **Tập d** cho kết quả tốt nhất. |
| **Cell 54** | **Grid Search toàn diện** | `p: 0..3`, `q: 0..3`, `P: 0..2`, `Q: 0..2`, `D: [0, 1]`, `s: [7]` | Tổng cộng **288 tổ hợp mô hình**. **Mất từ 15 đến 30 phút** tùy theo tốc độ CPU. |
| **Cell 56 & 58** | **Mô hình SARIMAX tối ưu nhất** | `order=(0, 1, 3)`, `seasonal_order=(1, 0, 2, 7)`, biến thời tiết tập `d` | Mô hình đạt kết quả vượt trội: **MAPE $\approx$ 2.90%**. |

> [!TIP]
> **Mẹo tiết kiệm thời gian chạy Cell 54 (Grid Search):**
> Cell 54 duyệt qua 288 mô hình để chứng minh thực nghiệm mô hình `(0, 1, 3)(1, 0, 2, 7)` là tốt nhất. Nếu bạn chỉ cần kiểm tra kết quả cuối cùng hoặc vẽ biểu đồ, bạn có thể **bỏ qua việc chạy Cell 54** và chạy thẳng đến **Cell 56** và **Cell 58** để khớp ngay mô hình tối ưu.

---

## 5. Hướng Dẫn Chi Tiết & Thiết Lập Thông Số Cho `NEW_models.ipynb`

Notebook này xây dựng pipeline hoàn chỉnh cho Deep Learning: đọc dữ liệu nhanh bằng DuckDB, chuẩn hóa, tạo cửa sổ trượt (Sliding Windows) và huấn luyện hai kiến trúc mạng nơ-ron: **LSTM** và **Transformer**.

### 5.1. Thiết lập cấu hình tổng thể (Cell 4)

Đoạn mã cấu hình đầu notebook:

```python
PARQUET_DIR      = '../../data'               # Sửa thành '../data' nếu data nằm ngang hàng
DEMAND_PATH      = f'{PARQUET_DIR}/demand.parquet'
METADATA_PATH    = f'{PARQUET_DIR}/metadata.parquet'
WEATHER_PATH     = f'{PARQUET_DIR}/weather.parquet'

LOOKBACK         = 365                        # Số ngày lịch sử dùng để dự đoán ngày tiếp theo
BATCH_SIZE       = 64                         # Kích thước batch huấn luyện (giảm xuống 32 nếu thiếu VRAM)
EPOCHS           = 100                        # Số epoch huấn luyện tối đa
PATIENCE         = 15                         # Dừng sớm nếu val_loss không giảm sau 15 epoch liên tiếp

CKPT_LSTM        = 'checkpoints_lstm'        # Thư mục lưu checkpoint LSTM
CKPT_TRANSFORMER = 'checkpoints_transformer' # Thư mục lưu checkpoint Transformer

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Device: {DEVICE}')
```

**Chi tiết các thông số cấu hình:**
- `PARQUET_DIR`: Đổi thành `'../data'` nếu thư mục dữ liệu ở `/home/jiooum/Downloads/data`.
- `LOOKBACK = 365`: Chiều dài chuỗi thời gian đầu vào (1 năm lịch sử), giúp mô hình học được cả tính chu kỳ tuần (7 ngày) và chu kỳ mùa trong năm (365 ngày).
- `BATCH_SIZE = 64`: Phù hợp với hầu hết GPU và CPU hiện đại. Nếu gặp lỗi `CUDA out of memory`, hãy đổi thành `32` hoặc `16`.
- `EPOCHS = 100`: Giới hạn trên của số chu kỳ học. Thông thường cơ chế Early Stopping sẽ dừng huấn luyện trong khoảng 25 - 45 epochs.
- `PATIENCE = 15`: Số epoch chờ trước khi kích hoạt Early Stopping.

---

### 5.2. Các đặc trưng đầu vào (9 Features - Cell 8)
Dữ liệu đầu vào cho các mô hình Deep Learning gồm 9 đặc trưng được chuẩn hóa bằng `StandardScaler`:
1. `soil_temperature_7_to_28cm`: Nhiệt độ đất ở độ sâu 7 - 28cm.
2. `soil_temperature_0_to_7cm`: Nhiệt độ đất ở độ sâu 0 - 7cm.
3. `apparent_temperature`: Nhiệt độ cảm nhận ngoài trời.
4. `temperature_2m`: Nhiệt độ không khí ở độ cao 2m.
5. `y`: Giá trị tiêu thụ điện trung bình trong quá khứ (Autoregressive feature).
6. `day_of_week_sin` & `day_of_week_cos`: Biến đổi chu kỳ lượng giác cho thứ trong tuần (0 đến 6).
7. `day_of_year_sin` & `day_of_year_cos`: Biến đổi chu kỳ lượng giác cho ngày trong năm (1 đến 365).

---

### 5.3. Chi tiết mô hình & Siêu tham số huấn luyện

#### A. Mô hình LSTM (Cell 19 - 21)
- **Kiến trúc**:
  - `input_size = 9`, `hidden_size = 128`, `num_layers = 2`, `dropout = 0.2`.
  - Head dự báo: `Sequential(Linear(128, 64), ReLU(), Dropout(0.2), Linear(64, 1))`.
  - Tổng số tham số: $\approx 211,009$.
- **Tối ưu hóa (Optimization)**:
  - **Hàm mất mát**: `nn.HuberLoss(delta=1.0)` (bền vững trước các điểm ngoại lai hơn MSE).
  - **Optimizer**: `torch.optim.AdamW(lr=1e-3, weight_decay=1e-4)`.
  - **Learning Rate Scheduler**:
    - 5 epochs đầu: `LinearLR` (Warmup tăng dần từ $0.1 \times lr$ lên $1.0 \times lr$).
    - Các epochs sau: `CosineAnnealingLR` giảm dần về `eta_min=1e-6`.

#### B. Mô hình Transformer (Cell 28 - 30)
- **Kiến trúc**:
  - `input_size = 9`, `d_model = 64`, `nhead = 4`.
  - `num_encoder_layers = 2`, `dim_feedforward = 128`, `dropout = 0.3`.
  - Cơ chế gộp chuỗi (Pooling): `AttentionPooling` (tự học trọng số đóng góp của từng bước thời gian thay vì chỉ lấy điểm cuối cùng).
  - Head dự báo: `Sequential(LayerNorm(64), Linear(64, 1))`.
  - Tổng số tham số: $\approx 68,546$.
- **Tối ưu hóa (Optimization)**:
  - **Optimizer**: `torch.optim.AdamW(lr=4e-4, weight_decay=1e-3)`.
  - **Gradient Clipping**: `grad_clip_max_norm = 1.0` (ngăn bùng nổ gradient trong mạng tự chú ý).
  - **Scheduler**: Tương tự (5 epochs Linear Warmup $\rightarrow$ Cosine Annealing).

---

### 5.4. Lựa chọn: Huấn luyện mới hay Sử dụng Checkpoint có sẵn?

Dự án đã có sẵn các file weights đã được huấn luyện tối ưu trong thư mục `checkpoints_lstm/best.pt` và `checkpoints_transformer/best.pt`.

#### Lựa chọn 1: Huấn luyện lại từ đầu
Chạy bình thường các cell từ trên xuống dưới (chạy Cell 21 để train LSTM, Cell 30 để train Transformer). Quá trình sẽ lưu đè các checkpoint mới vào thư mục tương ứng.

#### Lựa chọn 2: Sử dụng Checkpoint có sẵn (Đánh giá ngay lập tức)
Nếu bạn không muốn đợi huấn luyện 100 epochs, sau khi chạy đến Cell 19 (khởi tạo LSTM) và Cell 28 (khởi tạo Transformer), bạn có thể chèn đoạn mã sau để nạp trọng số đã lưu:

```python
# --- Nạp trọng số có sẵn cho LSTM ---
ckpt_lstm = torch.load('checkpoints_lstm/best.pt', map_location=DEVICE, weights_only=False)
lstm.load_state_dict(ckpt_lstm['model_state_dict'])
print(f"Đã nạp checkpoint LSTM tốt nhất tại epoch {ckpt_lstm['epoch']}")

# --- Nạp trọng số có sẵn cho Transformer ---
ckpt_tr = torch.load('checkpoints_transformer/best.pt', map_location=DEVICE, weights_only=False)
transformer.load_state_dict(ckpt_tr['model_state_dict'])
print(f"Đã nạp checkpoint Transformer tốt nhất tại epoch {ckpt_tr['epoch']}")
```
Sau đó bạn có thể bỏ qua Cell 21 và Cell 30, nhảy trực tiếp đến các cell đánh giá (Cell 25, Cell 34 và Cell 41) để quan sát kết quả.

---

## 6. Tổng Hợp Kết Quả Đánh Giá Giữa Các Mô Hình

Kết quả kiểm thử trên tập Test (từ `2024-01-01` đến `2025-01-01`):

| Mô hình | Phương pháp | MAPE (%) | RMSE | Đặc điểm nổi bật |
| :--- | :--- | :---: | :---: | :--- |
| **SARIMAX (0, 1, 3)(1, 0, 2, 7)** | Thống kê + Biến thời tiết ngoại sinh | **2.90%** | ~6.75 | Nắm bắt chu kỳ tuần và hiệu ứng thời tiết rất tốt, thời gian suy luận tức thì. |
| **LSTM (2 layers, 128 hidden)** | Học sâu chuỗi thời gian đệ quy | **2.90%** | **6.7067** | Khả năng ghi nhớ thông tin dài hạn xuất sắc, độ lệch chuẩn sai số thấp nhất. |
| **Transformer Forecast** | Attention Pooling Encoder | **4.73%** | 10.3382 | Số lượng tham số ít hơn ($~68K$ vs $~211K$), tốc độ tính toán song song nhanh. |

---

## 7. Khắc Phục Sự Cố Thường Gặp (Troubleshooting / FAQ)

### 1. Lỗi `FileNotFoundError: [Errno 2] No such file or directory: '../../data/metadata.parquet'`
- **Nguyên nhân**: Đường dẫn tương đối `../../data` trỏ ra ngoài 2 cấp thư mục, trong khi thư mục `data` nằm ở vị trí khác.
- **Cách xử lý**:
  - Trong `SARIMAX.ipynb` (Cell 2): Sửa `parquet_directory = '../data'`.
  - Trong `NEW_models.ipynb` (Cell 4): Sửa `PARQUET_DIR = '../data'`.
  - Hoặc tạo symbolic link ngay trong thư mục code:
    ```bash
    ln -s /home/jiooum/Downloads/data ./data
    # Sau đó đổi path trong notebook thành './data'
    ```

### 2. Lỗi `ModuleNotFoundError: No module named 'pmdarima'` hoặc `'duckdb'`
- **Nguyên nhân**: Kernel Jupyter đang chọn không trùng với môi trường ảo đã cài đặt thư viện.
- **Cách xử lý**:
  1. Kiểm tra lại môi trường trong terminal: `which python` và `pip list`.
  2. Đảm bảo đã chạy `python -m ipykernel install --user ...`.
  3. Trên giao diện Jupyter, vào menu **Kernel** $\rightarrow$ **Change Kernel** $\rightarrow$ Chọn đúng tên kernel `elec_forecast`.

### 3. Lỗi `CUDA out of memory` trong `NEW_models.ipynb`
- **Nguyên nhân**: Dung lượng VRAM của card đồ họa không đủ cho `BATCH_SIZE = 64` kết hợp chuỗi `LOOKBACK = 365`.
- **Cách xử lý**: Giảm `BATCH_SIZE` trong Cell 4 xuống `32` hoặc `16`:
  ```python
  BATCH_SIZE = 32
  ```

### 4. Tập dữ liệu Test trong SARIMAX bị nhân đôi kích thước
- **Nguyên nhân**: Bạn đã chạy Cell 47 nhiều lần trong một phiên làm việc mà không khởi động lại kernel.
- **Cách xử lý**: Chọn **Kernel** $\rightarrow$ **Restart Kernel and Run Up to Selected Cell**, hoặc chạy lại tuần tự từ Cell 13.

### 5. Quá trình chạy `SARIMAX.ipynb` bị treo hoặc quá lâu ở Cell 54
- **Nguyên nhân**: Cell 54 chạy Grid Search qua 288 mô hình SARIMAX bằng CPU.
- **Cách xử lý**: Dừng cell đó (bấm nút Stop/Interrupt Kernel), sau đó chạy thẳng xuống Cell 56 và Cell 58 để khớp mô hình tối ưu đã được định sẵn.
