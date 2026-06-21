# دستیار بررسی آگهی ملک

داشبورد فارسی Streamlit برای دریافت آگهی‌های خرید مسکونی، فیلتر بودجه و متراژ،
ذخیره در SQLite، نقشه و عامل هوشمند شخصی‌سازی‌شده.

## اجرا

در Ubuntu/Debian، اگر ساخت محیط مجازی خطا داد ابتدا `python3-venv` را نصب کنید.

```bash
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run main.py
```

ورودی قبلی نیز سازگار است:

```bash
streamlit run app.py
```

برای تحلیل هوشمند، `OPENAI_API_KEY` را در `.env` قرار دهید. بدون کلید هم برنامه
با رتبه‌بندی ساده قیمت اجرا می‌شود.

## Agent Mode و حافظه

ابتدا حساب کاربری بسازید یا وارد شوید. سپس «عامل هوشمند» را انتخاب و درخواست را
طبیعی بنویسید، برای نمونه:

```text
یک آپارتمان در تهران تا ۵ میلیارد و حداقل ۸۰ متر می‌خواهم
```

عامل شهر، بودجه و متراژ را استخراج و سه پیشنهاد را با breakdown قابل توضیح
نمایش می‌دهد. بدون کلید OpenAI، parser قانون‌محور فارسی/انگلیسی فعال می‌شود.

بودجه، شهرها، حداقل متراژ، جست‌وجوها و املاک پسندیده/ردشده به شناسه داخلی حساب
متصل و در SQLite ذخیره می‌شوند. رمز عبور به شکل `scrypt` hash می‌شود و متن خام
آن هرگز ذخیره نمی‌شود.

## استان و شهر

در Filter Mode ابتدا استان و سپس شهر را انتخاب کنید. catalog عمومی دیوار شامل
بیش از هزار شهر دریافت و هفت روز در SQLite cache می‌شود. در قطع شبکه، آخرین cache
یا فهرست ۳۱ مرکز استان استفاده خواهد شد.

رابط کاربری از فایل‌های محلی فونت Yekan استفاده می‌کند و برای نمایش فونت به CDN
وابسته نیست.

نقشه با PyDeck نمایش داده می‌شود. برای آگهی‌های بدون مختصات، سرویس Nominatim
با نرخ محدود و cache محلی استفاده می‌شود؛ در صورت قطع شبکه، موقعیت تقریبی نزدیک
مرکز شهر جایگزین خواهد شد. برای غیرفعال‌کردن درخواست geocoding، مقدار
`GEOCODING_ENABLED=false` را در `.env` قرار دهید.

## معماری

```text
app/
  agents/     # natural-language real estate agent
  auth/       # registration, login, and password hashing
  core/       # parsing and formatting utilities
  db/         # SQLite repository
  memory/     # persistent user profile and interaction memory
  models/     # domain models
  providers/  # listing source adapters
  services/   # filtering, ranking, and orchestration
  ui/         # Streamlit dashboard, components, and map view
main.py       # primary entry point
app.py        # backward-compatible entry point
```

برای افزودن منبع جدید، interface موجود در `app/providers/base.py` را پیاده‌سازی
و provider را هنگام ساخت `SearchService` تزریق کنید.

## تست

```bash
pip install -r requirements-dev.txt
pytest -q
```

## نکات مهم

- اتصال فعلی دیوار یک کلاینت دفاعی برای پاسخ جست‌وجوی عمومی است و API شریک تضمین‌شده نیست.
- برای محصول واقعی باید مجوز/مسیر رسمی هر منبع، نرخ درخواست و شرایط استفاده بررسی شود.
- آگهی‌ها داده قابل اعتماد حقوقی نیستند؛ قیمت، مالکیت، سند و وضعیت بنا باید جداگانه بررسی شوند.
