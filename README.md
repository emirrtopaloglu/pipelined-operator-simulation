# Araba Üretim Simülatörü

Bu proje, bir araba üretim hattının pipeline (boru hattı) mantığıyla nasıl çalıştığını simüle eden bir masaüstü uygulamasıdır.

## Gereksinimler

*   Python 3.x
*   PySide6

## Kurulum

1.  Proje dosyalarını bilgisayarınıza indirin veya klonlayın.
2.  Gerekli kütüphaneyi yükleyin:
    ```sh
    pip install PySide6
    ```

## Çalıştırma

Uygulamayı başlatmak için aşağıdaki komutu terminalde çalıştırın:

```sh
python app.py
```

Uygulama açıldığında:
1.  İsteğe bağlı olarak virgülle ayrılmış şasi numaraları girebilirsiniz. Boş bırakırsanız, otomatik olarak şasi numaraları atanacaktır.
2.  Üretilecek araba sayısını seçin (varsayılan 5, maksimum 20).
3.  Simülasyon hızını milisaniye cinsinden ayarlayın (varsayılan 1000 ms).
4.  "Başlat" düğmesine tıklayarak simülasyonu başlatın.

Pipeline tablosu, her bir arabanın üretim aşamalarındaki ilerlemesini saat döngüsü bazında gösterecektir. "Üretilen Arabalar" listesi ise üretim hattından çıkan arabaları listeleyecektir.