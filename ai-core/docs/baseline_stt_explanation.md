# Baseline STT — Giải thích Chi tiết Script Phiên âm Whisper

> **Script:** `ai-core/scripts/run_baseline_stt.py`
>
> **Output:** `ai-core/data/processed/custom_baseline_labels.csv`

---

## 1. Mục đích của Script

Script này thực hiện bước **Speech-to-Text (STT)** đầu tiên trong pipeline đánh giá phát âm tiếng Anh:

| Bước | Mô tả |
|------|--------|
| **Input** | Các file ghi âm `.wav` (16 kHz, Mono) của người nói — định dạng IELTS Speaking (Part 1 / 2 / 3). |
| **Xử lý** | Dùng mô hình Whisper để phiên âm tự động (ASR) toàn bộ audio thành văn bản tiếng Anh. |
| **Output** | File CSV chứa: tên file, bản phiên âm Whisper, cột `ground_truth` (để trống — sẽ được điền thủ công sau), và thời gian xử lý. |

### Vai trò trong Pipeline tổng thể

```
[Audio .wav] ──▶ [STT / Whisper] ──▶ [Transcript CSV]
                                           │
                        ┌──────────────────┘
                        ▼
              [So sánh với Ground Truth]
                        │
                        ▼
              [Tính WER / CER Metrics]
                        │
                        ▼
              [Đánh giá chất lượng ASR]
```

Bản phiên âm tự động sẽ được so sánh với **ground truth** (bản chép tay chính xác) để tính các chỉ số lỗi như **WER (Word Error Rate)** và **CER (Character Error Rate)**. Kết quả này giúp:

1. **Đánh giá năng lực baseline** — hiểu Whisper "nghe" giọng Việt nói tiếng Anh tốt đến đâu mà không cần fine-tune.
2. **Xác định lỗi phát âm phổ biến** — những từ bị Whisper nghe sai thường là những từ mà người Việt phát âm chưa chuẩn (ví dụ: /θ/ → /t/, /ʃ/ → /s/).
3. **Làm cơ sở dữ liệu** cho các bước training và evaluation tiếp theo.

---

## 2. Về OpenAI Whisper

### 2.1 Whisper là gì?

**Whisper** là một mô hình **Automatic Speech Recognition (ASR)** do OpenAI phát triển và công bố mã nguồn mở vào tháng 9/2022.

- **GitHub:** [https://github.com/openai/whisper](https://github.com/openai/whisper)
- **Paper:** Radford, A., Kim, J. W., Xu, T., Brockman, G., McLeavey, C., & Sutskever, I. (2022). *Robust Speech Recognition via Large-Scale Weak Supervision*. [arXiv:2212.04356](https://arxiv.org/abs/2212.04356)

### 2.2 Đặc điểm chính

| Đặc điểm | Chi tiết |
|-----------|----------|
| **Kiến trúc** | Encoder-Decoder Transformer |
| **Dữ liệu huấn luyện** | ~680,000 giờ audio đa ngôn ngữ thu thập từ web |
| **Khả năng** | Nhận dạng giọng nói, dịch thuật, phát hiện ngôn ngữ, phân đoạn timestamp |
| **Ngôn ngữ** | Hỗ trợ 99 ngôn ngữ (bao gồm cả tiếng Việt) |
| **License** | MIT — sử dụng tự do cho cả nghiên cứu và thương mại |

### 2.3 Các model size

| Model | Params | VRAM cần | Tốc độ tương đối |
|-------|--------|----------|-------------------|
| `tiny` | 39 M | ~1 GB | ~32× |
| `base` | 74 M | ~1 GB | ~16× |
| `small` | 244 M | ~2 GB | ~6× |
| `medium` | 769 M | ~5 GB | ~2× |
| `large-v3` | 1550 M | ~10 GB | 1× |

---

## 3. Quyết định Kiến trúc — Tại sao chọn `base`?

Đây là phần quan trọng nhất: **trade-off analysis** để giải thích lý do chọn model `base` cho bước baseline này.

### 3.1 Mục tiêu của bước Baseline

Mục tiêu **không phải** là đạt accuracy cao nhất, mà là:

- Tạo transcript nhanh để xây dựng pipeline end-to-end.
- Đo lường zero-shot performance trên giọng Việt nói tiếng Anh.
- Có kết quả tham chiếu để so sánh khi nâng cấp model sau này.

### 3.2 Ma trận Trade-off

| Tiêu chí | `tiny` | **`base`** ✅ | `small` | `medium` | `large-v3` |
|-----------|--------|--------------|---------|----------|-------------|
| **Tốc độ inference** | Rất nhanh | Nhanh | Trung bình | Chậm | Rất chậm |
| **VRAM yêu cầu** | ~1 GB | ~1 GB | ~2 GB | ~5 GB | ~10 GB |
| **Chạy được trên CPU** | ✅ Tốt | ✅ Chấp nhận | ⚠️ Chậm | ❌ Rất chậm | ❌ Không thực tế |
| **WER trên English** | Cao (~12%) | Khá (~10%) | Tốt (~7%) | Rất tốt (~5%) | Xuất sắc (~3%) |
| **Phù hợp baseline** | Quá kém | **Cân bằng** | Tốt nhưng chậm | Overkill | Overkill |

> *Lưu ý: WER ước lượng dựa trên benchmark của OpenAI trên tập LibriSpeech (native English). Với accented speech (giọng Việt), WER thực tế sẽ cao hơn đáng kể.*

### 3.3 Lý do loại bỏ các model khác

#### ❌ `tiny` — Quá kém cho accented speech

- Chỉ 39M params — khả năng xử lý non-native accent rất hạn chế.
- Nhiều từ bị hallucinate hoặc bỏ sót, khiến ground truth annotation trở nên vô nghĩa.
- Tiết kiệm vài giây nhưng hy sinh quá nhiều chất lượng.

#### ❌ `small` — Tốt nhưng chưa cần ở giai đoạn này

- 244M params, cần ~2 GB VRAM — vẫn chạy được nhưng chậm hơn đáng kể trên CPU.
- Accuracy tốt hơn `base` ~3% WER, nhưng cho mục đích baseline thì `base` đã đủ.
- Sẽ cân nhắc ở giai đoạn evaluation chính thức.

#### ❌ `medium` / `large-v3` — Quá nặng cho local development

- `medium` cần ~5 GB VRAM, `large-v3` cần ~10 GB — vượt quá khả năng của nhiều máy dev.
- Chạy trên CPU thì thời gian xử lý quá lâu (mỗi file có thể mất vài phút).
- Dành cho production hoặc inference trên GPU chuyên dụng.

### 3.4 Kết luận

**`base` là lựa chọn tối ưu cho baseline** vì:

1. **VRAM thấp (~1 GB)** — chạy được trên hầu hết máy tính cá nhân, kể cả CPU.
2. **Tốc độ chấp nhận được** — xử lý 15 file audio trong vài phút.
3. **Accuracy đủ tốt** — WER ~10% trên native English, đủ để phân biệt các lỗi phát âm rõ ràng.
4. **Reproducible** — ai cũng có thể chạy lại mà không cần GPU đắt tiền.

---

## 4. Hướng dẫn Chạy

### 4.1 Yêu cầu hệ thống

- **Python** ≥ 3.9
- **FFmpeg** (Whisper cần FFmpeg để decode audio)
  ```bash
  # Windows (winget)
  winget install Gyan.FFmpeg

  # macOS
  brew install ffmpeg

  # Ubuntu/Debian
  sudo apt install ffmpeg
  ```
- **CUDA** (không bắt buộc) — nếu có GPU NVIDIA, script tự động dùng CUDA để tăng tốc.

### 4.2 Cài đặt Dependencies

```bash
# Từ thư mục gốc project
pip install -r ai-core/requirements.txt
```

Các package chính cần thiết:

```
openai-whisper==20231117
torch>=2.1.0
tqdm>=4.66.0
```

### 4.3 Chạy Script

```bash
# Từ thư mục gốc project (D:\speaking_app)
python ai-core/scripts/run_baseline_stt.py
```

### 4.4 Output mong đợi

```
=================================================================
  Baseline STT — OpenAI Whisper Transcription
=================================================================
  Model   : whisper-base
  Device  : cuda          (hoặc "cpu")
  Files   : 15 .wav files
-----------------------------------------------------------------
Transcribing: 100%|██████████████████| 15/15 [01:23<00:00, 5.55s/file]

-----------------------------------------------------------------
  Done!  Transcribed: 15/15 files
  Total processing time : 83.25s
  Output saved to       : D:\speaking_app\ai-core\data\processed\custom_baseline_labels.csv
-----------------------------------------------------------------
```

### 4.5 Cấu trúc File CSV đầu ra

| file_name | whisper_transcript | ground_truth | processing_time |
|---|---|---|---|
| 001_P1_studying.wav | I am currently studying... | *(điền sau)* | 5.23 |
| 001_P1_visit.wav | The last place I visited... | *(điền sau)* | 4.87 |
| ... | ... | ... | ... |

> **Bước tiếp theo:** Mở file CSV, nghe lại từng audio và điền cột `ground_truth` bằng tay. Sau đó chạy script tính WER/CER để đánh giá.

---

## 5. Tham khảo

1. Radford, A. et al. (2022). *Robust Speech Recognition via Large-Scale Weak Supervision*. [arXiv:2212.04356](https://arxiv.org/abs/2212.04356)
2. OpenAI Whisper GitHub: [https://github.com/openai/whisper](https://github.com/openai/whisper)
3. L2-ARCTIC Corpus: [https://psi.engr.tamu.edu/l2-arctic-corpus/](https://psi.engr.tamu.edu/l2-arctic-corpus/)
