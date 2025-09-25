# MatcherApp

MatcherApp — настільна програма для локальної звірки товарних прайсів між «моїм» прайсом та прайсами постачальників. Застосунок працює офлайн, підтримує нормалізацію брендів/моделей/типів плівок, strict та fuzzy матчинг з блокуванням, а також експорт результатів у CSV.

## Можливості

- Імпорт CSV/XLSX файлів мого прайсу та декількох прайсів постачальників.
- Автоматичне визначення колонок з можливістю ручного мапінгу.
- Нормалізація текстових полів, побудова blocking-ключів.
- Комбінований strict та fuzzy матчинг з конфігурованими вагами та порогами.
- Класифікація рядків на Exact / Near / Unmatched, генерація `canon_id` (опційно).
- Експорт результатів у CSV (utf-8-sig).
- Логування у файл `matcher.log` з ротацією.

## Вимоги

- Python 3.11
- Windows 10/11 (рекомендовано для GUI та збірки `.exe`).

## Встановлення

```bat
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Запуск із вихідного коду

```bat
.venv\Scripts\activate
python main.py
```

Або скористайтесь скриптом:

```bat
run.bat
```

## Збірка виконуваного файлу

```bat
.venv\Scripts\activate
pyinstaller --noconfirm --clean --onefile --windowed --name "MatcherApp" --icon icon.ico main.py
```

Або:

```bat
build.bat
```

Готовий `MatcherApp.exe` з'явиться в каталозі `dist`.

## Приклад даних

### «Мій прайс» (CSV)

| Назва позиції           | Виробник | Модель         | Тип плівки   | Артикул | Ціна |
|-------------------------|----------|----------------|--------------|---------|------|
| Захисна плівка iPhone   | Apple    | iPhone 13      | матова       | A13-MAT | 299  |
| Захисна плівка Samsung  | Samsung  | Galaxy S22     | прозора      | S22-CLR | 249  |
| Захисна плівка Redmi    | Xiaomi   | Redmi Note 11  | anti blue    | RN11-AB | 189  |

### Прайс постачальника (XLSX)

| Наименование           | Производитель | Device Model  | Series        | SKU      | Price |
|------------------------|----------------|---------------|---------------|----------|-------|
| Film iPhone 13 Matte   | Apple          | iPhone 13     | matte         | APP-13-M | 305   |
| Film Galaxy S22 Clear  | Samsung        | Galaxy S22    | clear         | SAM-S22C | 250   |
| Film Redmi Note 11 AB  | Xiaomi         | Redmi Note 11 | anti-blue     | XM-RN11A | 195   |

Ці приклади демонструють різні назви колонок (українська/російська/англійська), що дозволяє перевірити автоматичне визначення та ручне мапування.

## Структура проєкту

```
matcher_app/
  main.py
  run.bat
  build.bat
  icon.ico
  matcher/
    __init__.py
    config.py
    core.py
    exporters.py
    hashid.py
    io_utils.py
    logging_utils.py
    matching.py
    models.py
    normalization.py
    ui_app.py
```

## Конфігурація

Після першого запуску поруч із `main.py` буде створено `config.json`, де зберігаються користувацькі мапінги колонок і, за потреби, оновлені пороги/ваги.

## Ліцензія

Проєкт призначений як MVP і може модифікуватися відповідно до внутрішніх потреб команди.
