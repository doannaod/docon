"""Çeviri sözlüğü: Türkçe kaynak metin -> {"en": ..., "es": ...}.

app/core/i18n.py tarafından kullanılır. Yeni bir arayüz metni eklerken buraya
da ekle (anahtar birebir kaynak koddaki Türkçe metinle aynı olmalı, {placeholder}
adları da dahil).
"""
from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    # --- genel / navigasyon ---
    "Ana Sayfa": {"en": "Home", "es": "Inicio"},
    "Geçmiş İşler": {"en": "History", "es": "Historial"},
    "Ayarlar": {"en": "Settings", "es": "Configuración"},
    "Ortam denetleniyor…": {"en": "Checking environment…", "es": "Comprobando el entorno…"},
    "Program hazır": {"en": "Program ready", "es": "Programa listo"},
    "İlk kurulum bekliyor": {"en": "Waiting for first-time setup", "es": "Esperando la configuración inicial"},

    # --- ana ekran (home.py) ---
    "Kitaplar": {"en": "Books", "es": "Libros"},
    "Sıraya PDF ekle, sürükleyerek sırala, tıklayıp sağda incele.": {
        "en": "Add PDFs to the queue, drag to reorder, click one to review it on the right.",
        "es": "Añade PDF a la cola, arrastra para reordenar, haz clic para revisarlo a la derecha.",
    },
    "Henüz kitap eklenmedi. PDF'leri sürükle ya da Dosya Ekle'ye bas.": {
        "en": "No books added yet. Drag PDFs here or click Add File.",
        "es": "Aún no se han añadido libros. Arrastra PDF aquí o pulsa Añadir archivo.",
    },
    "Dosya Ekle": {"en": "Add File", "es": "Añadir archivo"},
    "veya PDF'leri buraya sürükle": {"en": "or drag PDFs here", "es": "o arrastra PDF aquí"},
    "Seçili kitap için:": {"en": "For the selected book:", "es": "Para el libro seleccionado:"},
    "Adını değiştir": {"en": "Rename", "es": "Cambiar nombre"},
    "Dosyayı değiştir": {"en": "Change file", "es": "Cambiar archivo"},
    "Sıradan kaldır": {"en": "Remove from queue", "es": "Quitar de la cola"},
    "Son dönüştürülenler": {"en": "Recently converted", "es": "Convertidos recientemente"},
    "Tümünü gör": {"en": "See all", "es": "Ver todo"},
    "Henüz dönüştürülmüş kitap yok.": {"en": "No books converted yet.", "es": "Todavía no se ha convertido ningún libro."},
    "Klasörü aç": {"en": "Open folder", "es": "Abrir carpeta"},
    "Klasör taşınmış": {"en": "Folder moved", "es": "La carpeta se movió"},
    "SEÇİLİ KİTAP": {"en": "SELECTED BOOK", "es": "LIBRO SELECCIONADO"},
    "Bir kitap seç": {"en": "Select a book", "es": "Selecciona un libro"},
    "Zorunlu OCR (force_ocr)": {"en": "Force OCR (force_ocr)", "es": "Forzar OCR (force_ocr)"},
    "Öneriye dön": {"en": "Reset to recommendation", "es": "Volver a la recomendación"},
    "Çıktı klasörü": {"en": "Output folder", "es": "Carpeta de salida"},
    "Gözat…": {"en": "Browse…", "es": "Examinar…"},
    "Klasöre Git": {"en": "Open Folder", "es": "Ir a la carpeta"},
    "Kitap dosyaları bu klasörde.": {"en": "The book's files are in this folder.", "es": "Los archivos del libro están en esta carpeta."},
    "Kitap klasörü adın altında oluşur. Kök klasör son kullanılan yerdir; Gözat ile değiştir.": {
        "en": "The book's folder is created under its name. The root folder is the last one used; change it with Browse.",
        "es": "La carpeta del libro se crea bajo su nombre. La carpeta raíz es la última usada; cámbiala con Examinar.",
    },
    "Test koşusu ({n} sayfa)": {"en": "Test run ({n} pages)", "es": "Prueba ({n} páginas)"},
    "Dönüştür": {"en": "Convert", "es": "Convertir"},
    "Test yapılmamış kitaplar önce {n} sayfa test edilir, sonra tam koşuya geçer.": {
        "en": "Books that haven't been tested are first tested with {n} pages, then run in full.",
        "es": "Los libros sin probar se prueban primero con {n} páginas y luego se convierten por completo.",
    },
    "{n} kitabı sırayla dönüştür": {"en": "Convert {n} books in order", "es": "Convertir {n} libros en orden"},
    "Çıktı kök klasörünü seç": {"en": "Choose the output root folder", "es": "Elige la carpeta raíz de salida"},
    "PDF kitapları seç": {"en": "Select PDF books", "es": "Selecciona libros PDF"},
    "PDF dosyaları (*.pdf)": {"en": "PDF files (*.pdf)", "es": "Archivos PDF (*.pdf)"},
    "Açık": {"en": "On", "es": "Activado"},
    "Kapalı": {"en": "Off", "es": "Desactivado"},
    "öneri": {"en": "recommended", "es": "recomendado"},
    "elle": {"en": "manual", "es": "manual"},
    "{n} sayfa": {"en": "{n} pages", "es": "{n} páginas"},

    # --- describe_book (home.py) ---
    "Test koşusu: ilk {n} sayfa çevrildi": {"en": "Test run: first {n} pages converted", "es": "Prueba: primeras {n} páginas convertidas"},
    "Metin katmanı temiz.": {"en": "Text layer is clean.", "es": "La capa de texto está limpia."},
    "Kitap taranmış görünüyor.": {"en": "The book appears to be scanned.", "es": "El libro parece estar escaneado."},
    "Metin katmanı var ama bozuk.": {"en": "There's a text layer but it's broken.", "es": "Hay capa de texto pero está dañada."},
    "{p} sayfada {denklem} denklem, {tablo} tablo satırı, {resim} şekil;": {
        "en": "In {p} pages: {denklem} equations, {tablo} table rows, {resim} figures;",
        "es": "En {p} páginas: {denklem} ecuaciones, {tablo} filas de tabla, {resim} figuras;",
    },
    "boş denklem yok": {"en": "no empty equations", "es": "sin ecuaciones vacías"},
    "{n} boş denklem": {"en": "{n} empty equations", "es": "{n} ecuaciones vacías"},
    "bozuk karakter yok.": {"en": "no broken characters.", "es": "sin caracteres dañados."},
    "{n} bozuk karakter.": {"en": "{n} broken characters.", "es": "{n} caracteres dañados."},
    "İçindekiler ağacı var: {n} başlık.": {"en": "Table of contents found: {n} headings.", "es": "Índice encontrado: {n} títulos."},
    "İçindekiler ağacı yok, 40 sayfalık parçalara bölünecek.": {
        "en": "No table of contents; it will be split into 40-page parts.",
        "es": "Sin índice; se dividirá en partes de 40 páginas.",
    },
    "metin katmanı temiz, hızlı mod yeterli": {"en": "text layer is clean, fast mode is enough", "es": "la capa de texto está limpia, el modo rápido basta"},
    "test çıktısında bozuk denklem veya karakter görüldü, her sayfa görüntü olarak okunacak": {
        "en": "broken equations or characters were seen in the test output, every page will be read as an image",
        "es": "se detectaron ecuaciones o caracteres dañados en la prueba, cada página se leerá como imagen",
    },
    "sayfalarda çok az okunabilir metin var, kitap taranmış görünüyor": {
        "en": "pages have very little readable text, the book appears to be scanned",
        "es": "las páginas tienen muy poco texto legible, el libro parece escaneado",
    },
    "metin katmanı güvenilir değil, her sayfa görüntü olarak okunacak": {
        "en": "the text layer isn't reliable, every page will be read as an image",
        "es": "la capa de texto no es fiable, cada página se leerá como imagen",
    },
    "kullanıcı elle seçti": {"en": "manually chosen by the user", "es": "elegido manualmente por el usuario"},
    "{choice}: Zorunlu OCR {state}; {why}.": {"en": "{choice}: Force OCR {state}; {why}.", "es": "{choice}: OCR forzado {state}; {why}."},
    "Seçim": {"en": "Choice", "es": "Elección"},
    "Öneri": {"en": "Recommendation", "es": "Recomendación"},
    "açık": {"en": "on", "es": "activado"},
    "kapalı": {"en": "off", "es": "desactivado"},
    "Tahmini süre yaklaşık {sure}.": {"en": "Estimated time is about {sure}.", "es": "Tiempo estimado de unos {sure}."},
    "Hızlı inceleme (test koşusu henüz yapılmadı)": {
        "en": "Quick review (test run not done yet)", "es": "Revisión rápida (prueba aún no realizada)",
    },
    "Metin katmanı: {tl}. Tür: {kind}. İçindekiler: {outline}.": {
        "en": "Text layer: {tl}. Kind: {kind}. Table of contents: {outline}.",
        "es": "Capa de texto: {tl}. Tipo: {kind}. Índice: {outline}.",
    },
    "Öneri: {reason}": {"en": "Recommendation: {reason}", "es": "Recomendación: {reason}"},
    "İnceleniyor…": {"en": "Analyzing…", "es": "Analizando…"},
    "PDF okunuyor, birkaç saniye sürer.": {"en": "Reading the PDF, this takes a few seconds.", "es": "Leyendo el PDF, tarda unos segundos."},

    # --- analyzer.py ---
    "Yok veya çok az": {"en": "None or very little", "es": "Ninguna o muy poca"},
    "Var, bozuk": {"en": "Present, broken", "es": "Presente, dañada"},
    "Var, temiz": {"en": "Present, clean", "es": "Presente, limpia"},
    "Taranmış (görüntü)": {"en": "Scanned (image)", "es": "Escaneado (imagen)"},
    "Dijital (taranmamış)": {"en": "Digital (not scanned)", "es": "Digital (sin escanear)"},
    "Yok (40 sayfalık parça)": {"en": "None (40-page parts)", "es": "Ninguno (partes de 40 páginas)"},
    "{n} başlık": {"en": "{n} headings", "es": "{n} títulos"},
    "Sayfaların çoğunda metin katmanı yok, kitap taranmış görünüyor. Her sayfa görüntü olarak işlenecek; daha yavaş ama doğru.": {
        "en": "Most pages have no text layer, the book appears to be scanned. Every page will be processed as an image; slower but accurate.",
        "es": "La mayoría de las páginas no tienen capa de texto, el libro parece escaneado. Cada página se procesará como imagen; más lento pero preciso.",
    },
    "Metin katmanı var ama bozuk karakterler içeriyor (denklem ve indisler yanlış çıkabilir). Zorunlu OCR daha doğru sonuç verir.": {
        "en": "There's a text layer but it contains broken characters (equations and subscripts may come out wrong). Forcing OCR gives more accurate results.",
        "es": "Hay capa de texto pero contiene caracteres dañados (ecuaciones e índices pueden salir mal). Forzar el OCR da resultados más precisos.",
    },
    "Metin katmanı temiz, hızlı mod yeterli. Denklemler bozuk çıkarsa açabilirsin.": {
        "en": "Text layer is clean, fast mode is enough. You can turn it on if equations come out broken.",
        "es": "La capa de texto está limpia, el modo rápido basta. Puedes activarlo si las ecuaciones salen mal.",
    },

    # --- settings.py ---
    "Değişiklikler anında kaydedilir.": {"en": "Changes are saved instantly.", "es": "Los cambios se guardan al instante."},
    "Dil": {"en": "Language", "es": "Idioma"},
    "Arayüz dili": {"en": "Interface language", "es": "Idioma de la interfaz"},
    "Dil değişikliğinin uygulanması için programı yeniden başlat.": {
        "en": "Restart the program for the language change to take effect.",
        "es": "Reinicia el programa para que el cambio de idioma surta efecto.",
    },
    "Çıktı": {"en": "Output", "es": "Salida"},
    "Varsayılan çıktı klasörü (son kullanılan otomatik gelir)": {
        "en": "Default output folder (the last one used is set automatically)",
        "es": "Carpeta de salida predeterminada (se usa automáticamente la última utilizada)",
    },
    "Kitap bitince Windows bildirimi göster": {"en": "Show a Windows notification when a book is done", "es": "Mostrar una notificación de Windows al terminar un libro"},
    "Motor": {"en": "Engine", "es": "Motor"},
    "Sistem varsayılanları önerilir": {"en": "System defaults are recommended", "es": "Se recomiendan los valores predeterminados del sistema"},
    "Blok boyutu (sayfa)": {"en": "Block size (pages)", "es": "Tamaño de bloque (páginas)"},
    "Parça boyutu (sayfa)": {"en": "Part size (pages)", "es": "Tamaño de parte (páginas)"},
    "Test koşusu (sayfa)": {"en": "Test run (pages)", "es": "Prueba (páginas)"},
    "varsayılan {d}": {"en": "default {d}", "es": "predeterminado {d}"},
    "Varsayılan: {d}": {"en": "Default: {d}", "es": "Predeterminado: {d}"},
    "Blok: OCR kaç sayfalık parçalarla yapılır. Parça: içindekiler yoksa kitap kaç sayfalık dosyalara bölünür.": {
        "en": "Block: how many pages OCR processes at a time. Part: how many pages per file when there's no table of contents.",
        "es": "Bloque: cuántas páginas procesa el OCR a la vez. Parte: cuántas páginas por archivo cuando no hay índice.",
    },
    "Varsayılanlara dön": {"en": "Reset to defaults", "es": "Restablecer valores predeterminados"},
    "Depolama": {"en": "Storage", "es": "Almacenamiento"},
    "Ham klasörleri temizle": {"en": "Clean up raw folders", "es": "Limpiar carpetas sin procesar"},
    "Temizle": {"en": "Clean up", "es": "Limpiar"},
    "Bitmiş kitapların ara dosyaları. {n} kitap · {size}. Silmek çıktıyı etkilemez.": {
        "en": "Intermediate files of finished books. {n} books · {size}. Deleting them doesn't affect the output.",
        "es": "Archivos intermedios de libros terminados. {n} libros · {size}. Borrarlos no afecta la salida.",
    },
    "Temizlenecek ara dosya yok.": {"en": "No intermediate files to clean up.", "es": "No hay archivos intermedios que limpiar."},
    "✓ Silindi, {size} boşaldı.": {"en": "✓ Deleted, {size} freed up.", "es": "✓ Eliminado, {size} liberados."},
    "Varsayılan çıktı klasörü": {"en": "Default output folder", "es": "Carpeta de salida predeterminada"},

    # --- setup.py (ilk kurulum) ---
    "Hoş geldin. Program ilk kez açılıyor.": {"en": "Welcome. The program is starting for the first time.", "es": "Bienvenido. El programa se inicia por primera vez."},
    "Kitap çevirmeye başlamadan önce bir kerelik hazırlık gerekiyor. Bu ekran yalnızca ilk açılışta görünür.": {
        "en": "A one-time setup is needed before converting books. This screen only appears the first time.",
        "es": "Se necesita una preparación única antes de convertir libros. Esta pantalla solo aparece la primera vez.",
    },
    "Yaklaşık {gb} GB indirilecek. Başlayalım mı?": {"en": "About {gb} GB will be downloaded. Shall we start?", "es": "Se descargarán unos {gb} GB. ¿Empezamos?"},
    "<b>Neden gerekli:</b> PDF sayfalarını okuyup Markdown'a çeviren yapay zekâ modelleri (surya) ve onları ekran kartında çalıştıran yazılım (torch, marker) programın içinde gelmiyor; boyutları yüzünden bir kez internetten indirilir ve bilgisayarında kalır. Sonraki açılışlarda tekrar inmez.": {
        "en": "<b>Why it's needed:</b> the AI models that read PDF pages and convert them to Markdown (surya), and the software that runs them on your graphics card (torch, marker), don't come bundled with the app; due to their size they're downloaded once from the internet and stay on your computer. They won't download again on later launches.",
        "es": "<b>Por qué es necesario:</b> los modelos de IA que leen las páginas del PDF y las convierten a Markdown (surya), y el software que los ejecuta en tu tarjeta gráfica (torch, marker), no vienen incluidos en el programa; por su tamaño se descargan una vez de internet y quedan en tu ordenador. No volverán a descargarse en próximos inicios.",
    },
    "Terminal açmana veya elle bir şey kurmana gerek yok. Bağlantı koparsa indirme kaldığı yerden devam eder. İndirme bitince bildirim alırsın; sonra istediğin zaman kitap ekleyip çevirebilirsin.": {
        "en": "You don't need to open a terminal or install anything manually. If the connection drops, the download resumes where it left off. You'll get a notification when it's done; you can add and convert books whenever you want after that.",
        "es": "No necesitas abrir una terminal ni instalar nada manualmente. Si se corta la conexión, la descarga continúa donde se quedó. Recibirás una notificación cuando termine; después podrás añadir y convertir libros cuando quieras.",
    },
    "Sonra (programı gez)": {"en": "Later (explore the app)", "es": "Más tarde (explorar la app)"},
    "İndirmeyi başlat": {"en": "Start download", "es": "Iniciar descarga"},
    "Toplam ilerleme": {"en": "Overall progress", "es": "Progreso total"},
    "İnternet hızı": {"en": "Internet speed", "es": "Velocidad de internet"},
    "Tahmini kalan süre": {"en": "Estimated time left", "es": "Tiempo restante estimado"},
    "İnen / toplam": {"en": "Downloaded / total", "es": "Descargado / total"},
    "Bağlantı koparsa indirme kaldığı yerden devam eder.": {
        "en": "If the connection drops, the download resumes where it left off.",
        "es": "Si se corta la conexión, la descarga continúa donde se quedó.",
    },
    "Yeniden dene": {"en": "Retry", "es": "Reintentar"},
    "Duraklat": {"en": "Pause", "es": "Pausar"},
    "İlk kurulum: gereken yazılım ve modeller iniyor": {
        "en": "First-time setup: downloading the required software and models",
        "es": "Configuración inicial: descargando el software y los modelos necesarios",
    },
    "Bu işlem yalnızca bir kez yapılır. Bittiğinde bildirim alırsın; kitap çevirmeye o zaman başlarsın.": {
        "en": "This is only done once. You'll get a notification when it's done, then you can start converting books.",
        "es": "Esto solo se hace una vez. Recibirás una notificación al terminar, y podrás empezar a convertir libros.",
    },
    "Tamamlandı": {"en": "Done", "es": "Completado"},
    "İniyor…": {"en": "Downloading…", "es": "Descargando…"},
    "Hata": {"en": "Error", "es": "Error"},
    "Bekliyor": {"en": "Waiting", "es": "Esperando"},
    "hesaplanıyor…": {"en": "calculating…", "es": "calculando…"},
    "{h} sa {m} dk": {"en": "{h} h {m} min", "es": "{h} h {m} min"},
    "{m} dk {s} sn": {"en": "{m} min {s} s", "es": "{m} min {s} s"},
    "Devam et": {"en": "Resume", "es": "Continuar"},

    # --- convert.py ---
    "EKRAN KARTI": {"en": "GRAPHICS CARD", "es": "TARJETA GRÁFICA"},
    "Sıcaklık": {"en": "Temperature", "es": "Temperatura"},
    "Kullanım": {"en": "Usage", "es": "Uso"},
    "Bellek (VRAM)": {"en": "Memory (VRAM)", "es": "Memoria (VRAM)"},
    "2 sn'de bir güncellenir": {"en": "Updates every 2 seconds", "es": "Se actualiza cada 2 segundos"},
    "SIRA": {"en": "QUEUE", "es": "COLA"},
    "… dönüştürülüyor": {"en": "… converting", "es": "… convirtiendo"},
    "Aşama 1 / 2: OCR": {"en": "Stage 1 / 2: OCR", "es": "Etapa 1 / 2: OCR"},
    "Aşama 2 / 2: Bölme": {"en": "Stage 2 / 2: Splitting", "es": "Etapa 2 / 2: División"},
    "Blok — / —": {"en": "Block — / —", "es": "Bloque — / —"},
    "Geçen süre": {"en": "Elapsed time", "es": "Tiempo transcurrido"},
    "0 sn": {"en": "0 s", "es": "0 s"},
    "Bu kitap için kalan": {"en": "Left for this book", "es": "Restante para este libro"},
    "Sıradaki kitaplar": {"en": "Next books", "es": "Próximos libros"},
    "Şu an": {"en": "Right now", "es": "Ahora mismo"},
    "Durdurursan biten bloklar saklanır. Bilgisayar bu sırada uyumaz.": {
        "en": "If you stop, finished blocks are kept. The computer won't sleep in the meantime.",
        "es": "Si detienes, los bloques terminados se conservan. El ordenador no entrará en reposo mientras tanto.",
    },
    "Bu kitabı atla": {"en": "Skip this book", "es": "Omitir este libro"},
    "Durdur": {"en": "Stop", "es": "Detener"},
    "Kitap {i} / {n}": {"en": "Book {i} / {n}", "es": "Libro {i} / {n}"},
    "test ediliyor": {"en": "testing", "es": "probando"},
    "dönüştürülüyor": {"en": "converting", "es": "convirtiendo"},
    "Başladı {now} · Zorunlu OCR {state}": {"en": "Started {now} · Force OCR {state}", "es": "Iniciado {now} · OCR forzado {state}"},
    "Sırada: Aşama 2 / 2 Bölme.": {"en": "Next: Stage 2 / 2 Splitting.", "es": "Siguiente: Etapa 2 / 2 División."},
    "Sırada: Aşama 2 / 2 Bölme. İçindekiler bulundu, gerçek bölümlere ayrılacak.": {
        "en": "Next: Stage 2 / 2 Splitting. Table of contents found, it will be split into real chapters.",
        "es": "Siguiente: Etapa 2 / 2 División. Índice encontrado, se dividirá en capítulos reales.",
    },
    "Sırada: Aşama 2 / 2 Bölme. İçindekiler yok, 40 sayfalık parçalara ayrılacak.": {
        "en": "Next: Stage 2 / 2 Splitting. No table of contents, it will be split into 40-page parts.",
        "es": "Siguiente: Etapa 2 / 2 División. Sin índice, se dividirá en partes de 40 páginas.",
    },
    " · sayfalar {a}–{b}": {"en": " · pages {a}–{b}", "es": " · páginas {a}–{b}"},
    "Blok {cur} / {total}": {"en": "Block {cur} / {total}", "es": "Bloque {cur} / {total}"},
    "yok": {"en": "none", "es": "ninguno"},
    "Hazırlanıyor…": {"en": "Preparing…", "es": "Preparando…"},
    "Durduruluyor…": {"en": "Stopping…", "es": "Deteniendo…"},

    # --- done.py ---
    "… hazır": {"en": "… ready", "es": "… listo"},
    "Yüklenen PDF": {"en": "Uploaded PDF", "es": "PDF cargado"},
    "Bölüm dosyası": {"en": "Chapter file", "es": "Archivo de capítulo"},
    "Şekil ve grafik": {"en": "Figures and charts", "es": "Figuras y gráficos"},
    "Üretilen dosyalar": {"en": "Generated files", "es": "Archivos generados"},
    "Yeni Kitap Ekle": {"en": "Add New Book", "es": "Añadir nuevo libro"},
    "{name} hazır": {"en": "{name} ready", "es": "{name} listo"},
    " · toplam {n} kitap bitti": {"en": " · {n} books done in total", "es": " · {n} libros completados en total"},
    "Tamamlandı {t} · Toplam süre {sure} · Zorunlu OCR {state}": {
        "en": "Finished {t} · Total time {sure} · Force OCR {state}", "es": "Terminado {t} · Tiempo total {sure} · OCR forzado {state}",
    },
    "Kalite taraması: {q}": {"en": "Quality scan: {q}", "es": "Análisis de calidad: {q}"},
    "{n} + {ek} ek": {"en": "{n} + {ek} appendix", "es": "{n} + {ek} anexo"},
    "Çıktı klasörü bulunamadı. Taşınmış ya da silinmiş olabilir.": {
        "en": "Output folder not found. It may have been moved or deleted.",
        "es": "No se encontró la carpeta de salida. Puede que se haya movido o eliminado.",
    },
    "00-index.md · birimler, alt kısımlar, tablo ve şekil listesi": {
        "en": "00-index.md · units, sub-sections, list of tables and figures",
        "es": "00-index.md · unidades, subsecciones, lista de tablas y figuras",
    },
    "birlesik.md · kitabın tamamı tek dosyada": {"en": "birlesik.md · the whole book in one file", "es": "birlesik.md · todo el libro en un archivo"},
    "sekiller\\ · {n} görsel": {"en": "sekiller\\ · {n} images", "es": "sekiller\\ · {n} imágenes"},

    # --- history.py (UI) ---
    "Kitap": {"en": "Book", "es": "Libro"},
    "Tarih": {"en": "Date", "es": "Fecha"},
    "Süre": {"en": "Duration", "es": "Duración"},
    "PDF → Çıktı": {"en": "PDF → Output", "es": "PDF → Salida"},
    "Kaydedildiği yer": {"en": "Saved to", "es": "Guardado en"},
    "Durum": {"en": "Status", "es": "Estado"},
    "Geçmiş İşler": {"en": "History", "es": "Historial"},
    "Kitap adında ara": {"en": "Search by book name", "es": "Buscar por nombre de libro"},
    "Bir iş seç": {"en": "Select a job", "es": "Selecciona un trabajo"},
    "Ayrıntılı günlük": {"en": "Detailed log", "es": "Registro detallado"},
    "Kaldığı yerden devam et": {"en": "Resume where it left off", "es": "Continuar donde se quedó"},
    "Bugüne kadar dönüştürülen {done} kitap, {half} yarım kalan iş": {
        "en": "{done} books converted so far, {half} jobs left unfinished",
        "es": "{done} libros convertidos hasta ahora, {half} trabajos sin terminar",
    },
    "Ayrıntıları görmek için listeden bir kitap seç.": {
        "en": "Select a book from the list to see the details.", "es": "Selecciona un libro de la lista para ver los detalles.",
    },
    "Seçili: {name}": {"en": "Selected: {name}", "es": "Seleccionado: {name}"},
    "{n} blok": {"en": "{n} blocks", "es": "{n} bloques"},
    "Zorunlu OCR {state}": {"en": "Force OCR {state}", "es": "OCR forzado {state}"},
    "{ch} bölüm, {ek} ek": {"en": "{ch} chapters, {ek} appendices", "es": "{ch} capítulos, {ek} anexos"},
    "{n} şekil": {"en": "{n} figures", "es": "{n} figuras"},

    # --- status labels (queue.py / history.py) ---
    "Test bekliyor": {"en": "Waiting for test", "es": "Esperando prueba"},
    "Test sürüyor": {"en": "Testing", "es": "Probando"},
    "Test tamam": {"en": "Test done", "es": "Prueba lista"},
    "Dönüştürülüyor": {"en": "Converting", "es": "Convirtiendo"},
    "Bitti": {"en": "Done", "es": "Listo"},
    "Atlandı": {"en": "Skipped", "es": "Omitido"},
    "Sürüyor": {"en": "Running", "es": "En curso"},
    "Yarım kaldı": {"en": "Left half-done", "es": "Quedó a medias"},
    "Yarım {done}/{total}": {"en": "Half {done}/{total}", "es": "A medias {done}/{total}"},

    # --- history.py (core: date/duration) ---
    "Oca": {"en": "Jan", "es": "ene"}, "Şub": {"en": "Feb", "es": "feb"}, "Mar": {"en": "Mar", "es": "mar"},
    "Nis": {"en": "Apr", "es": "abr"}, "May": {"en": "May", "es": "may"}, "Haz": {"en": "Jun", "es": "jun"},
    "Tem": {"en": "Jul", "es": "jul"}, "Ağu": {"en": "Aug", "es": "ago"}, "Eyl": {"en": "Sep", "es": "sep"},
    "Eki": {"en": "Oct", "es": "oct"}, "Kas": {"en": "Nov", "es": "nov"}, "Ara": {"en": "Dec", "es": "dic"},
    "{n} sn": {"en": "{n} s", "es": "{n} s"},
    "{n} dk": {"en": "{n} min", "es": "{n} min"},

    # --- main_window.py ---
    "Yeni sürüm mevcut: {tag}. Ayarlar'dan indirme sayfasını açabilirsin.": {
        "en": "A new version is available: {tag}. You can open the download page from Settings.",
        "es": "Hay una nueva versión disponible: {tag}. Puedes abrir la página de descarga desde Ajustes.",
    },
    "Yeni sürüm mevcut: {tag}": {"en": "New version available: {tag}", "es": "Nueva versión disponible: {tag}"},
    "Disk: {free} GB boş, ~{need} GB gerekir · {gpu}": {
        "en": "Disk: {free} GB free, ~{need} GB needed · {gpu}", "es": "Disco: {free} GB libres, ~{need} GB necesarios · {gpu}",
    },
    "Hazır": {"en": "Ready", "es": "Listo"},
    "Kitabın adı": {"en": "Book title", "es": "Título del libro"},
    "Bu ad hem listede hem çıktı klasöründe kullanılır:": {
        "en": "This name is used both in the list and in the output folder:",
        "es": "Este nombre se usa tanto en la lista como en la carpeta de salida:",
    },
    "PDF seç": {"en": "Select PDF", "es": "Selecciona PDF"},
    "Dosya yolu değişmiş.\n\nKitap klasörü artık burada değil:\n{p}\n\nTaşındıysa yeni yerinden açabilirsin; geçmiş kaydı eski yolu gösterir.": {
        "en": "The file path has changed.\n\nThe book folder is no longer here:\n{p}\n\nIf it was moved, you can open it from its new location; the history entry shows the old path.",
        "es": "La ruta del archivo ha cambiado.\n\nLa carpeta del libro ya no está aquí:\n{p}\n\nSi se movió, puedes abrirla desde su nueva ubicación; el historial muestra la ruta antigua.",
    },
    "Klasör bulunamadı:\n{p}": {"en": "Folder not found:\n{p}", "es": "Carpeta no encontrada:\n{p}"},
    "GPU: {name}": {"en": "GPU: {name}", "es": "GPU: {name}"},
    "NVIDIA GPU bulunamadı (çok yavaş çalışır)": {"en": "No NVIDIA GPU found (runs very slowly)", "es": "No se encontró GPU NVIDIA (funciona muy lento)"},
    "C: sürücüsü {free} GB boş, 12 GB gerekir · {gpu}": {
        "en": "C: drive {free} GB free, 12 GB needed · {gpu}", "es": "Unidad C: {free} GB libres, se necesitan 12 GB · {gpu}",
    },
    "Kurulum durdu: {m}": {"en": "Setup stopped: {m}", "es": "La instalación se detuvo: {m}"},
    "Duraklatıldı. 'Devam et' ile kaldığı yerden sürer.": {
        "en": "Paused. Use 'Resume' to continue where it left off.", "es": "Pausado. Usa 'Continuar' para seguir donde se quedó.",
    },
    "Kurulum tamamlandı. Program kullanıma hazır.": {"en": "Setup complete. The program is ready to use.", "es": "Instalación completa. El programa está listo para usar."},
    "Program kullanıma hazır": {"en": "Program ready to use", "es": "Programa listo para usar"},
    "Gereken yazılım ve modeller indi. Artık kitap ekleyip çevirebilirsin.": {
        "en": "The required software and models have downloaded. You can now add and convert books.",
        "es": "El software y los modelos necesarios se han descargado. Ya puedes añadir y convertir libros.",
    },
    "Kurulum tamamlandı. Program kullanıma hazır.\nKitap eklemek için Ana Sayfa'ya dönülüyor.": {
        "en": "Setup complete. The program is ready to use.\nReturning to Home to add a book.",
        "es": "Instalación completa. El programa está listo para usar.\nVolviendo a Inicio para añadir un libro.",
    },
    "Benzetim": {"en": "Simulation", "es": "Simulación"},
    "Kurulum bitti görünüyor ama ortam denetimi geçemedi. 'Yeniden dene' ile tekrar kontrol edilir.": {
        "en": "Setup appears finished but the environment check failed. Use 'Retry' to check again.",
        "es": "La instalación parece terminada pero la comprobación del entorno falló. Usa 'Reintentar' para comprobar de nuevo.",
    },
    "PDF bulunamadı:\n{p}": {"en": "PDF not found:\n{p}", "es": "PDF no encontrado:\n{p}"},
    "Yazıldı: {ad}": {"en": "Written: {ad}", "es": "Escrito: {ad}"},
    "Motor başlatılıyor…": {"en": "Starting the engine…", "es": "Iniciando el motor…"},
    "Blok {k} hata verdi (kod {rc})": {"en": "Block {k} failed (code {rc})", "es": "El bloque {k} falló (código {rc})"},
    "Blok {k} için marker başlatıldı (sayfa {a}–{b})": {
        "en": "Marker started for block {k} (pages {a}–{b})", "es": "Marker iniciado para el bloque {k} (páginas {a}–{b})",
    },
    "{pages} sayfa, {total} blok": {"en": "{pages} pages, {total} blocks", "es": "{pages} páginas, {total} bloques"},
    "Blok {k} tamamlandı ({sec})": {"en": "Block {k} completed ({sec})", "es": "Bloque {k} completado ({sec})"},
    "OCR bitti, bölme aşaması başladı": {"en": "OCR finished, splitting stage started", "es": "OCR terminado, comenzó la etapa de división"},
    "İçindekiler bulundu: {ch} bölüm, {other} ek": {
        "en": "Table of contents found: {ch} chapters, {other} appendices", "es": "Índice encontrado: {ch} capítulos, {other} anexos",
    },
    "İçindekiler yok, {other} sayfalık parçalara bölünüyor": {
        "en": "No table of contents, splitting into {other}-page parts", "es": "Sin índice, dividiendo en partes de {other} páginas",
    },
    "Bazı bloklar hata verdi; 'Kaldığı yerden devam et' ile eksikler tamamlanabilir.": {
        "en": "Some blocks failed; use 'Resume where it left off' to complete the missing parts.",
        "es": "Algunos bloques fallaron; usa 'Continuar donde se quedó' para completar lo que falta.",
    },
    "{sure} sürdü · {kalite}": {"en": "took {sure} · {kalite}", "es": "tardó {sure} · {kalite}"},
    "kalite taraması yapıldı": {"en": "quality scan done", "es": "análisis de calidad realizado"},
    "Tüm kitaplar bitti": {"en": "All books done", "es": "Todos los libros completados"},
    "{n} kitap dönüştürüldü.": {"en": "{n} books converted.", "es": "{n} libros convertidos."},
    "Dönüştürme durdu:\n{msg}": {"en": "Conversion stopped:\n{msg}", "es": "La conversión se detuvo:\n{msg}"},
    "Kullanıcı durdurdu.": {"en": "Stopped by the user.", "es": "Detenido por el usuario."},
    "Bu iş için henüz günlük dosyası yok.": {"en": "There's no log file for this job yet.", "es": "Todavía no hay archivo de registro para este trabajo."},
    "Dönüştürme sürüyor. Kapatırsan biten bloklar saklanır ve sonra devam edebilirsin.\nKapatılsın mı?": {
        "en": "A conversion is running. If you close, finished blocks are kept and you can resume later.\nClose anyway?",
        "es": "Hay una conversión en curso. Si cierras, los bloques terminados se conservan y podrás continuar después.\n¿Cerrar de todos modos?",
    },
    "Program kapatıldı.": {"en": "Program was closed.", "es": "El programa se cerró."},
    "{name} zaten açık. Görev çubuğundaki pencereyi kullan.": {
        "en": "{name} is already open. Use the window in the taskbar.",
        "es": "{name} ya está abierto. Usa la ventana en la barra de tareas.",
    },

    # --- environment.py / system.py / installer.py (kurulum) ---
    "Python çalışma ortamı": {"en": "Python runtime", "es": "Entorno de Python"},
    "torch (CUDA 12.6) ve marker-pdf {v}": {"en": "torch (CUDA 12.6) and marker-pdf {v}", "es": "torch (CUDA 12.6) y marker-pdf {v}"},
    "surya modelleri: metin tespiti, tanıma, düzen, tablo": {
        "en": "surya models: text detection, recognition, layout, tables", "es": "modelos surya: detección de texto, reconocimiento, diseño, tablas",
    },
    "Kurulum doğrulaması": {"en": "Setup verification", "es": "Verificación de la instalación"},
    "GPU bulunamadı (CPU, yavaş)": {"en": "No GPU found (CPU, slow)", "es": "No se encontró GPU (CPU, lento)"},
    "GPU: {name}, {gb} GB": {"en": "GPU: {name}, {gb} GB", "es": "GPU: {name}, {gb} GB"},
    "GPU yok": {"en": "No GPU", "es": "Sin GPU"},
    "Kurulum için C: sürücüsünde en az 12 GB boş alan gerekir, şu an {free} GB var.": {
        "en": "At least 12 GB of free space is needed on drive C: for setup, currently {free} GB is available.",
        "es": "Se necesitan al menos 12 GB libres en la unidad C: para la instalación, actualmente hay {free} GB disponibles.",
    },
    "Çıktı sürücüsünde {need} GB gerekiyor, {free} GB boş var.": {
        "en": "{need} GB is needed on the output drive, {free} GB is free.", "es": "Se necesitan {need} GB en la unidad de salida, hay {free} GB libres.",
    },
    "NVIDIA ekran kartı bulunamadı; dönüştürme işlemciyle çok yavaş olur.": {
        "en": "No NVIDIA graphics card found; conversion will be very slow on the CPU.",
        "es": "No se encontró tarjeta gráfica NVIDIA; la conversión será muy lenta con la CPU.",
    },
    "Ekran kartı belleği {gb} GB; marker 8 GB altında yavaşlayabilir.": {
        "en": "Graphics card memory is {gb} GB; marker may slow down under 8 GB.",
        "es": "La memoria de la tarjeta gráfica es de {gb} GB; marker puede ralentizarse por debajo de 8 GB.",
    },
    "işlem zaman aşımına uğradı": {"en": "the operation timed out", "es": "la operación agotó el tiempo de espera"},
    "Python çalışma ortamı indiriliyor…": {"en": "Downloading the Python runtime…", "es": "Descargando el entorno de Python…"},
    "Python açılıyor ve pip kuruluyor…": {"en": "Extracting Python and installing pip…", "es": "Extrayendo Python e instalando pip…"},
    "pip kurulamadı (kurulum.log)": {"en": "pip could not be installed (kurulum.log)", "es": "no se pudo instalar pip (kurulum.log)"},
    "pip paket planı alınamadı (kurulum.log)": {"en": "Could not get the pip install plan (kurulum.log)", "es": "No se pudo obtener el plan de instalación de pip (kurulum.log)"},
    "{gname}: paket listesi çözülüyor…": {"en": "{gname}: resolving package list…", "es": "{gname}: resolviendo lista de paquetes…"},
    "{gname}: {n} paket, {mb} MB indiriliyor…": {"en": "{gname}: downloading {n} packages, {mb} MB…", "es": "{gname}: descargando {n} paquetes, {mb} MB…"},
    "{gname}: kuruluyor (birkaç dakika sürebilir)…": {"en": "{gname}: installing (may take a few minutes)…", "es": "{gname}: instalando (puede tardar varios minutos)…"},
    "{gname} paketleri kurulamadı (kurulum.log)": {"en": "{gname} packages could not be installed (kurulum.log)", "es": "No se pudieron instalar los paquetes {gname} (kurulum.log)"},
    "surya modelleri indiriliyor (marker kendisi indirir, ilerleme klasör boyutundan izlenir)…": {
        "en": "Downloading surya models (marker downloads them itself; progress is tracked by folder size)…",
        "es": "Descargando modelos surya (marker los descarga por sí mismo; el progreso se sigue por el tamaño de la carpeta)…",
    },
    "Modeller {n} denemede indirilemedi. İnternet bağlantısını kontrol edip 'Yeniden dene'ye bas.": {
        "en": "The models could not be downloaded after {n} attempts. Check your internet connection and press 'Retry'.",
        "es": "No se pudieron descargar los modelos tras {n} intentos. Comprueba tu conexión a internet y pulsa 'Reintentar'.",
    },
    "Model indirme kesildi, {n}. yeniden deneme (tamamlanan dosyalar korunur)…": {
        "en": "Model download interrupted, retry {n} (completed files are kept)…",
        "es": "Descarga de modelos interrumpida, reintento {n} (los archivos completados se conservan)…",
    },
    "Kurulum doğrulanıyor…": {"en": "Verifying setup…", "es": "Verificando la instalación…"},
    "Doğrulama başarısız: paketler içe aktarılamadı (kurulum.log)": {
        "en": "Verification failed: packages could not be imported (kurulum.log)", "es": "Verificación fallida: no se pudieron importar los paquetes (kurulum.log)",
    },
    "Kurulum tamam. GPU: {gpu} · torch {v}": {"en": "Setup complete. GPU: {gpu} · torch {v}", "es": "Instalación completa. GPU: {gpu} · torch {v}"},
    "Kurulum tamam, ancak CUDA bulunamadı; dönüştürme CPU'da çok yavaş olur. torch {v}": {
        "en": "Setup complete, but CUDA was not found; conversion will be very slow on the CPU. torch {v}",
        "es": "Instalación completa, pero no se encontró CUDA; la conversión será muy lenta con la CPU. torch {v}",
    },
    "Beklenmeyen hata: {e}": {"en": "Unexpected error: {e}", "es": "Error inesperado: {e}"},
    "Benzetim: kurulum tamam.": {"en": "Simulation: setup complete.", "es": "Simulación: instalación completa."},
    "bağlantı erken kapandı": {"en": "the connection closed early", "es": "la conexión se cerró antes de tiempo"},

    # --- engine_runner.py ---
    "Motor {code} koduyla kapandı. Ayrıntı: {log}": {"en": "Engine exited with code {code}. Details: {log}", "es": "El motor terminó con código {code}. Detalles: {log}"},
    "Motor başlatılamadı ({err}). Python: {py}": {"en": "Engine could not start ({err}). Python: {py}", "es": "No se pudo iniciar el motor ({err}). Python: {py}"},

    # --- quality.py ---
    "{n} eksik resim": {"en": "{n} missing images", "es": "{n} imágenes faltantes"},
    "{n} dengesiz LaTeX": {"en": "{n} unbalanced LaTeX", "es": "{n} LaTeX desequilibrado"},
    "{n} zayıf tablo": {"en": "{n} weak tables", "es": "{n} tablas débiles"},
    "{n} tablo boşluğu": {"en": "{n} table spacing issues", "es": "{n} problemas de espaciado de tabla"},
    "Kusur bulunamadı": {"en": "No defects found", "es": "No se encontraron defectos"},
}
