# ASMAG++ Research Framework - Quick Start

## 1) Cài thư viện
Mở Command Prompt tại thư mục dự án:

```bat
pip install -r requirements.txt
```

## 2) Chạy demo nhanh không cần CDnet2014
Demo này tự tạo dữ liệu giả lập để kiểm tra code, pipeline, metrics, chart.

```bat
scripts\run_synthetic_demo.bat
```

Kết quả nằm trong:

```text
outputs\synthetic_demo\
```

## 3) Chạy thử trên CDnet2014 thật
Sửa file:

```text
configs\q2_core.yaml
```

Đặt đúng đường dẫn:

```yaml
dataset_root: "D:/THS Programing/06.6 ASMAG Project/dataset cdnet2014/archive/dataset"
```

Sau đó chạy:

```bat
scripts\run_cdnet_debug.bat
```

## 4) Giai đoạn chạy khuyến nghị

### Debug
- `synthetic_demo.yaml`
- chạy 1 video giả lập, rất nhanh.

### CDnet debug
- `q2_core.yaml`
- `frame_step: 5`
- `max_frames_per_video: 300`
- kiểm tra pipeline trên một phần dữ liệu.

### Báo cáo chính thức
- đổi `frame_step: 1`
- `max_frames_per_video: null`
- chạy đủ các category cần báo cáo.

## 5) Kết quả đầu ra chính

Mỗi lần chạy sinh:

```text
outputs/<experiment_name>/
├── frame_metrics.csv
├── summary_event_metrics.csv
├── summary_pixel_metrics.csv
├── summary_edge_metrics.csv
├── charts/
│   ├── event_f1_by_pipeline.png
│   ├── cdnet_fmeasure_by_pipeline.png
│   └── activation_rate_by_pipeline.png
└── qualitative/
```

## 6) Ghi chú
- Nếu chưa có YOLO model hoặc chưa cài ultralytics, code vẫn chạy bằng `MockDetector` để test framework.
- Khi muốn chạy YOLO thật, đặt `detector_mode: yolo` và khai báo model trong YAML.
