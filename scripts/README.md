# Scripts

Утилиты для обучения, экспорта и бенчмарков моделей.

## Скрипты

| Файл | Описание |
|------|----------|
| `export_echonet_seg_to_onnx.py` | Экспорт EchoNet-Dynamic в ONNX |
| `finetune_lv_seg.py` | Fine-tuning LV сегментации |
| `finetune_la_seg.py` | Fine-tuning LA сегментации |
| `train_ma_landmark.py` | Обучение landmark detection |
| `calibrate_echonet_norm.py` | Калибровка нормализации |
| `generate_manifest_from_gold.py` | Генерация манифеста из gold standard |
| `repair_gold_collisions.py` | Исправление коллизий в gold данных |
| `run_lv_auto_bench.py` | Запуск LV бенчмарка |
| `run_la_auto_bench.py` | Запуск LA бенчмарка |
| `run_tests.sh` | Обёртка для запуска тестов |
| `sonoforge.desktop` | Desktop entry для Linux |

## Экспорт модели

```bash
# Экспорт EchoNet в ONNX
python scripts/export_echonet_seg_to_onnx.py

# Fine-tuning
python scripts/finetune_lv_seg.py --data ./gold --epochs 50
```

## Бенчмарки

```bash
# LV
python scripts/run_lv_auto_bench.py

# LA
python scripts/run_la_auto_bench.py
```
