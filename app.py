import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QListWidget,
    QLineEdit, QPushButton, QSpinBox, QMessageBox, QHeaderView,
    QTabWidget, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush
from collections import deque

class Instruction:
    def __init__(self, chassis_no, stage_names):
        self.chassis_no = chassis_no
        self.stage_names = stage_names
        self.color = self.generate_color()
        # Tamamlanma zamanları
        self.pipelined_start_cycle = None
        self.pipelined_end_cycle = None
        self.single_cycle_start_cycle = None
        self.single_cycle_end_cycle = None
    
    def generate_color(self):
        # Daha koyu renkler kullan
        colors = [
            QColor(65, 105, 225),   # Koyu mavi
            QColor(34, 139, 34),    # Koyu yeşil
            QColor(255, 140, 0),    # Koyu turuncu
            QColor(220, 20, 60),    # Koyu kırmızı
            QColor(148, 0, 211),    # Koyu mor
            QColor(139, 69, 19),    # Kahverengi
        ]
        # Şasi numarasının son karakterini kullanarak renk seç
        try:
            index = int(self.chassis_no[-1]) % len(colors)
        except:
            index = hash(self.chassis_no) % len(colors)
        return colors[index]

    def get_stage_text(self, stage_index):
        return f"🚗 {self.chassis_no}"

STAGES = ['Bellekten Getir (Şasi Montajı)', 'Buyrukları Çöz (Motor Yerleştirme)', 'İşlemi Yürüt (Boya Uygulama)', 'Bellek Erişimi (Cam ve Kapı Montajı)', 'Sonucu Yaz (Kalite Kontrol)']
STAGE_SHORT = ['IF', 'ID', 'EX', 'MEM', 'WB']  # Kısa etiketler

class PipelineSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("İşlemci Simülatörü - Karşılaştırma Görünümü")
        self.setMinimumSize(1200, 700)

        # Pipelined için değişkenler
        self.pipeline = [None] * len(STAGES)
        self.instruction_queue = deque()
        self.completed_pipelined = []
        self.cycle = 1
        self.instruction_history = []
        self.pipeline_history = []

        # Single cycle için değişkenler
        self.single_cycle_queue = deque()
        self.single_cycle_completed = []
        self.single_cycle_current = None
        self.single_cycle_stage = 0
        self.single_cycle_history = []

        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulate_cycle)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Genel font stilini artır
        app_font = QApplication.font()
        app_font.setPointSize(12)  # Temel font boyutu
        QApplication.setFont(app_font)

        # Giriş alanı
        input_layout = QHBoxLayout()
        self.chassis_input = QLineEdit()
        self.chassis_input.setPlaceholderText("Şasi numaraları (virgülle ayır)")
        self.chassis_input.setStyleSheet("font-size: 17px;")
        
        chassis_label = QLabel("Şasi No Gir (Opsiyonel):")
        chassis_label.setStyleSheet("font-size: 17px; font-weight: bold;")
        input_layout.addWidget(chassis_label)
        input_layout.addWidget(self.chassis_input)

        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(20)
        self.count_input.setValue(5)
        self.count_input.setStyleSheet("font-size: 17px;")
        
        count_label = QLabel("Araba Sayısı:")
        count_label.setStyleSheet("font-size: 17px; font-weight: bold;")
        input_layout.addWidget(count_label)
        input_layout.addWidget(self.count_input)

        self.start_button = QPushButton("Başlat")
        self.start_button.clicked.connect(self.start_simulation)
        self.start_button.setStyleSheet("font-size: 17px; font-weight: bold; padding: 5px 10px;")
        input_layout.addWidget(self.start_button)

        self.reset_button = QPushButton("Sıfırla")
        self.reset_button.clicked.connect(self.reset_simulation)
        self.reset_button.setStyleSheet("font-size: 17px; font-weight: bold; padding: 5px 10px;")
        input_layout.addWidget(self.reset_button)

        speed_layout = QHBoxLayout()
        speed_label = QLabel("Hız:")
        speed_label.setStyleSheet("font-size: 17px; font-weight: bold;")
        speed_layout.addWidget(speed_label)
        
        self.speed_slider = QSpinBox()
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(1000)
        self.speed_slider.setSingleStep(100)
        self.speed_slider.setSuffix(" ms")
        self.speed_slider.setStyleSheet("font-size: 17px;")
        speed_layout.addWidget(self.speed_slider)
        input_layout.addLayout(speed_layout)

        main_layout.addLayout(input_layout)

        # Ana simülasyon alanı
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabBar::tab { font-size: 18px; font-weight: bold; height: 30px; }")
        
        # Tab 1: Pipeline Görünümü
        pipeline_tab = QWidget()
        pipeline_layout = QVBoxLayout(pipeline_tab)
        
        # İki simülasyonun yan yana görünümü
        simulation_layout = QHBoxLayout()
        
        # Sol taraf: Pipelined işlemci
        pipelined_layout = QVBoxLayout()
        pipelined_title = QLabel("Boru Hatlı (Pipelined) İşlemci Simülasyonu")
        pipelined_title.setAlignment(Qt.AlignCenter)
        pipelined_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        pipelined_layout.addWidget(pipelined_title)
        
        self.pipeline_table = QTableWidget()
        self.pipeline_table.setRowCount(0)
        self.pipeline_table.setColumnCount(0)
        self.pipeline_table.verticalHeader().setVisible(True)
        self.pipeline_table.setStyleSheet("QTableWidget { font-size: 17px; } QHeaderView::section { font-size: 17px; font-weight: bold; }")
        pipelined_layout.addWidget(self.pipeline_table)
        
        # Pipelined çıktı listesi
        pipelined_out_layout = QVBoxLayout()
        pipelined_out_label = QLabel("Üretilen Arabalar 🚘")
        pipelined_out_label.setAlignment(Qt.AlignCenter)
        pipelined_out_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        pipelined_out_layout.addWidget(pipelined_out_label)
        
        self.pipelined_output_list = QListWidget()
        self.pipelined_output_list.setStyleSheet("font-size: 17px;")
        pipelined_out_layout.addWidget(self.pipelined_output_list)
        pipelined_layout.addLayout(pipelined_out_layout)
        
        simulation_layout.addLayout(pipelined_layout, 1)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        simulation_layout.addWidget(line)
        
        # Sağ taraf: Tek vuruşlu işlemci
        single_cycle_layout = QVBoxLayout()
        single_cycle_title = QLabel("Tek Vuruşlu (Single-Cycle) İşlemci Simülasyonu")
        single_cycle_title.setAlignment(Qt.AlignCenter)
        single_cycle_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        single_cycle_layout.addWidget(single_cycle_title)
        
        self.single_cycle_table = QTableWidget()
        self.single_cycle_table.setRowCount(0)
        self.single_cycle_table.setColumnCount(0)
        self.single_cycle_table.verticalHeader().setVisible(True)
        self.single_cycle_table.setStyleSheet("QTableWidget { font-size: 17px; } QHeaderView::section { font-size: 17px; font-weight: bold; }")
        single_cycle_layout.addWidget(self.single_cycle_table)
        
        # Tek vuruşlu çıktı listesi
        single_cycle_out_layout = QVBoxLayout()
        single_cycle_out_label = QLabel("Üretilen Arabalar 🚘")
        single_cycle_out_label.setAlignment(Qt.AlignCenter)
        single_cycle_out_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        single_cycle_out_layout.addWidget(single_cycle_out_label)
        
        self.single_cycle_output_list = QListWidget()
        self.single_cycle_output_list.setStyleSheet("font-size: 17px;")
        single_cycle_out_layout.addWidget(self.single_cycle_output_list)
        single_cycle_layout.addLayout(single_cycle_out_layout)
        
        simulation_layout.addLayout(single_cycle_layout, 1)
        
        pipeline_layout.addLayout(simulation_layout)
        
        # Tab 2: Performans Karşılaştırması
        comparison_tab = QWidget()
        comparison_layout = QVBoxLayout(comparison_tab)
        
        performance_title = QLabel("İşlemci Mimarileri Performans Karşılaştırması")
        performance_title.setAlignment(Qt.AlignCenter)
        performance_title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 18px;")
        comparison_layout.addWidget(performance_title)
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(4)
        self.comparison_table.setHorizontalHeaderLabels(["Araç", "Boru Hatlı Tamamlanma", "Tek Vuruşlu Tamamlanma", "Hızlanma Oranı"])
        header = self.comparison_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.comparison_table.setStyleSheet("QTableWidget { font-size: 17px; } QHeaderView::section { font-size: 18px; font-weight: bold; }")
        comparison_layout.addWidget(self.comparison_table)
        
        # Performans özeti alanı
        self.summary_label = QLabel("Simülasyon Tamamlandığında Performans Özeti Burada Gösterilecek")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setStyleSheet("font-size: 16px; margin: 20px;")
        comparison_layout.addWidget(self.summary_label)
        
        # Tabları ekle
        tab_widget.addTab(pipeline_tab, "Simülasyon Görünümü")
        tab_widget.addTab(comparison_tab, "Performans Karşılaştırması")
        
        main_layout.addWidget(tab_widget)

        # Durum etiketi
        self.status_label = QLabel("Simülasyon Bekliyor...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; padding: 5px; background-color: #000; border-radius: 5px;")
        main_layout.addWidget(self.status_label)

        # Renk açıklamaları
        legend_layout = QHBoxLayout()
        legend_label = QLabel("Aşama Kısaltmaları:")
        legend_label.setStyleSheet("font-size: 17px; font-weight: bold;")
        legend_layout.addWidget(legend_label)
        
        for stage, short in zip(STAGES, STAGE_SHORT):
            label = QLabel(f"{short}: {stage}")
            label.setStyleSheet("font-size: 17px;")
            legend_layout.addWidget(label)
            legend_layout.addSpacing(10)
        
        main_layout.addLayout(legend_layout)

    def reset_simulation(self):
        self.timer.stop()
        self.status_label.setText("Simülasyon Sıfırlandı")
        
        # İlgili değişkenleri sıfırla
        self.pipeline = [None] * len(STAGES)
        self.instruction_queue.clear()
        self.completed_pipelined.clear()
        self.single_cycle_queue.clear()
        self.single_cycle_completed.clear()
        self.single_cycle_current = None
        self.single_cycle_stage = 0
        self.instruction_history.clear()
        self.pipeline_history.clear()
        self.single_cycle_history.clear()
        self.cycle = 1
        
        # Arayüzü temizle
        self.pipeline_table.setRowCount(0)
        self.pipeline_table.setColumnCount(0)
        self.single_cycle_table.setRowCount(0)
        self.single_cycle_table.setColumnCount(0)
        self.pipelined_output_list.clear()
        self.single_cycle_output_list.clear()
        self.comparison_table.setRowCount(0)
        self.summary_label.setText("Simülasyon Tamamlandığında Performans Özeti Burada Gösterilecek")

    def start_simulation(self):
        # Tüm değişkenleri sıfırla
        self.reset_simulation()
        
        # Kullanıcı girdilerini al
        user_input = self.chassis_input.text().strip()
        chassis_numbers = [x.strip() for x in user_input.split(',') if x.strip()]
        count = self.count_input.value()

        # Şasi numaralarını oluştur veya kontrol et
        if not chassis_numbers:
            chassis_numbers = [f"SH-{i+1:03}" for i in range(count)]
        if len(chassis_numbers) < count:
            QMessageBox.warning(self, "Hata", f"Yetersiz şasi numarası girdiniz. En az {count} adet gerekli.")
            return

        # Talimatları kuyruğa ekle
        for i in range(count):
            instr = Instruction(chassis_numbers[i], STAGES)
            self.instruction_queue.append(instr)
            self.single_cycle_queue.append(instr)
            self.instruction_history.append(instr)

        # Karşılaştırma tablosunu hazırla
        self.comparison_table.setRowCount(count)
        for i, instr in enumerate(self.instruction_history):
            self.comparison_table.setItem(i, 0, QTableWidgetItem(instr.chassis_no))
            for col in range(1, 4):
                self.comparison_table.setItem(i, col, QTableWidgetItem("-"))

        # Pipelined tabloyu hazırla
        self.pipeline_table.clear()
        self.pipeline_table.setRowCount(0)
        self.pipeline_table.setColumnCount(count)
        
        # Tablo sütun başlıklarını şasi numaraları olarak ayarla
        self.pipeline_table.setHorizontalHeaderLabels([f"Komut #{i+1}\n{instr.chassis_no}" for i, instr in enumerate(self.instruction_history)])
        
        # Sütun genişliklerini ayarla
        header = self.pipeline_table.horizontalHeader()
        for i in range(count):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        # Single-cycle tabloyu hazırla
        self.single_cycle_table.clear()
        self.single_cycle_table.setRowCount(0)
        self.single_cycle_table.setColumnCount(count)
        
        # Tablo sütun başlıklarını şasi numaraları olarak ayarla
        self.single_cycle_table.setHorizontalHeaderLabels([f"Komut #{i+1}\n{instr.chassis_no}" for i, instr in enumerate(self.instruction_history)])
        
        # Sütun genişliklerini ayarla
        header = self.single_cycle_table.horizontalHeader()
        for i in range(count):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        self.status_label.setText("🚗 Simülasyon Başladı...")
        
        # Zamanlayıcı hızını ayarla
        self.timer.start(self.speed_slider.value())

    def simulate_cycle(self):
        # Simülasyon tamamlandı mı kontrol et
        if (not self.instruction_queue and all(x is None for x in self.pipeline) and 
            not self.single_cycle_queue and self.single_cycle_current is None):
            self.timer.stop()
            self.status_label.setText("✅ Tüm arabalar üretim hattından çıktı!")
            self.update_performance_summary()
            return

        # Pipelined işlemci simülasyonu
        self.simulate_pipelined_cycle()
        
        # Single-cycle işlemci simülasyonu
        self.simulate_single_cycle()
        
        # Cycle sayısını artır
        self.cycle += 1
        
        # Durumu güncelle
        self.status_label.setText(f"🔄 Üretim Döngüsü: {self.cycle}")

    def simulate_pipelined_cycle(self):
        # Test Sürüşü (WB) aşamasındaki arabayı üretimden çıkar
        if self.pipeline[-1]:
            completed_instr = self.pipeline[-1]
            completed_instr.pipelined_end_cycle = self.cycle
            self.completed_pipelined.append(completed_instr)
            self.pipelined_output_list.addItem(f"🚘 {completed_instr.chassis_no} (Döngü: {self.cycle})")
            
            # Karşılaştırma tablosunu güncelle
            for i, instr in enumerate(self.instruction_history):
                if instr.chassis_no == completed_instr.chassis_no:
                    self.comparison_table.setItem(i, 1, QTableWidgetItem(f"Döngü {completed_instr.pipelined_end_cycle}"))
                    # Eğer tek vuruşlu da tamamlandıysa hızlanma oranını hesapla
                    if instr.single_cycle_end_cycle:
                        speedup = instr.single_cycle_end_cycle / instr.pipelined_end_cycle
                        self.comparison_table.setItem(i, 3, QTableWidgetItem(f"{speedup:.2f}x"))
        
        # Pipeline aşamalarını kaydır
        for i in range(len(STAGES)-1, 0, -1):
            self.pipeline[i] = self.pipeline[i-1]
        
        # Yeni arabayı pipeline'a al
        if self.instruction_queue:
            new_instr = self.instruction_queue.popleft()
            if new_instr.pipelined_start_cycle is None:
                new_instr.pipelined_start_cycle = self.cycle
            self.pipeline[0] = new_instr
        else:
            self.pipeline[0] = None
        
        # Pipeline durumunu kaydet
        current_pipeline = self.pipeline.copy()
        self.pipeline_history.append(current_pipeline)
        
        # Pipelined tabloyu güncelle
        self.update_pipelined_table()

    def simulate_single_cycle(self):
        # Eğer mevcut işlem tamamlandıysa
        if self.single_cycle_current:
            if self.single_cycle_stage >= len(STAGES) - 1:  # Tüm aşamaları tamamladı
                completed_instr = self.single_cycle_current
                completed_instr.single_cycle_end_cycle = self.cycle
                self.single_cycle_completed.append(completed_instr)
                self.single_cycle_output_list.addItem(f"🚘 {completed_instr.chassis_no} (Döngü: {self.cycle})")
                self.single_cycle_current = None
                self.single_cycle_stage = 0
                
                # Karşılaştırma tablosunu güncelle
                for i, instr in enumerate(self.instruction_history):
                    if instr.chassis_no == completed_instr.chassis_no:
                        self.comparison_table.setItem(i, 2, QTableWidgetItem(f"Döngü {completed_instr.single_cycle_end_cycle}"))
                        # Eğer pipelined da tamamlandıysa hızlanma oranını hesapla
                        if instr.pipelined_end_cycle:
                            speedup = instr.single_cycle_end_cycle / instr.pipelined_end_cycle
                            self.comparison_table.setItem(i, 3, QTableWidgetItem(f"{speedup:.2f}x"))
            else:
                # Bir sonraki aşamaya geç
                self.single_cycle_stage += 1
        
        # Eğer işlem yoksa ve kuyrukta işlem varsa, yeni işlemi başlat
        if self.single_cycle_current is None and self.single_cycle_queue:
            self.single_cycle_current = self.single_cycle_queue.popleft()
            if self.single_cycle_current.single_cycle_start_cycle is None:
                self.single_cycle_current.single_cycle_start_cycle = self.cycle
            self.single_cycle_stage = 0
        
        # Single-cycle tabloyu güncelle
        self.update_single_cycle_table()

    def update_pipelined_table(self):
        # Yeni bir satır ekle
        current_row = self.pipeline_table.rowCount()
        self.pipeline_table.setRowCount(current_row + 1)
        
        # Satır başlığını döngü numarası olarak ayarla
        self.pipeline_table.setVerticalHeaderItem(current_row, QTableWidgetItem(f"Döngü {self.cycle}"))
        
        # Her instructionın bu döngüdeki durumunu kontrol et
        for col, instruction in enumerate(self.instruction_history):
            # Bu sütunun bu satırdaki hücresi
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            
            # Bu döngüde bu instruction hangi aşamada?
            stage_index = None
            for i, instr in enumerate(self.pipeline):
                if instr and instr.chassis_no == instruction.chassis_no:
                    stage_index = i
                    break
            
            if stage_index is not None:
                # Bu instruction pipeline'da ve işleniyor
                stage_name = STAGE_SHORT[stage_index]
                item.setText(f"{stage_name}\n🚗 {instruction.chassis_no}")
                item.setBackground(instruction.color)
                item.setForeground(QColor(255, 255, 255))  # Beyaz metin rengi
                item.setToolTip(f"Şasi: {instruction.chassis_no}, Aşama: {STAGES[stage_index]}")
            elif instruction in self.completed_pipelined:
                # Bu instruction tamamlandı
                item.setText("✅")
                item.setToolTip(f"{instruction.chassis_no} üretim hattından çıktı")
            else:
                # Bu instruction henüz pipeline'a girmedi
                item.setText("")
                item.setToolTip("Bu araba henüz üretim hattına girmedi")
            
            self.pipeline_table.setItem(current_row, col, item)
        
        # Tabloyu düzenle
        self.pipeline_table.resizeRowsToContents()
        self.pipeline_table.scrollToBottom()  # En alttaki satırı göster

    def update_single_cycle_table(self):
        # Yeni bir satır ekle
        current_row = self.single_cycle_table.rowCount()
        self.single_cycle_table.setRowCount(current_row + 1)
        
        # Satır başlığını döngü numarası olarak ayarla
        self.single_cycle_table.setVerticalHeaderItem(current_row, QTableWidgetItem(f"Döngü {self.cycle}"))
        
        # Her instructionın bu döngüdeki durumunu kontrol et
        for col, instruction in enumerate(self.instruction_history):
            # Bu sütunun bu satırdaki hücresi
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            
            # Bu döngüde bu instruction aktif mi?
            if self.single_cycle_current and self.single_cycle_current.chassis_no == instruction.chassis_no:
                # Bu instruction işleniyor
                stage_name = STAGE_SHORT[self.single_cycle_stage]
                item.setText(f"{stage_name}\n🚗 {instruction.chassis_no}")
                item.setBackground(instruction.color)
                item.setForeground(QColor(255, 255, 255))  # Beyaz metin rengi
                item.setToolTip(f"Şasi: {instruction.chassis_no}, Aşama: {STAGES[self.single_cycle_stage]}")
            elif instruction in self.single_cycle_completed:
                # Bu instruction tamamlandı
                item.setText("✅")
                item.setToolTip(f"{instruction.chassis_no} üretim hattından çıktı")
            else:
                # Bu instruction henüz işleme girmedi
                item.setText("")
                item.setToolTip("Bu araba henüz işleme alınmadı")
            
            self.single_cycle_table.setItem(current_row, col, item)
        
        # Tabloyu düzenle
        self.single_cycle_table.resizeRowsToContents()
        self.single_cycle_table.scrollToBottom()  # En alttaki satırı göster

    def update_performance_summary(self):
        # Tüm komutların bitmesi sonrasında performans özeti
        if len(self.instruction_history) == 0:
            return
            
        # Ortalama tamamlanma süreleri
        avg_pipelined = sum(instr.pipelined_end_cycle for instr in self.instruction_history) / len(self.instruction_history)
        avg_single_cycle = sum(instr.single_cycle_end_cycle for instr in self.instruction_history) / len(self.instruction_history)
        
        # İlk ve son komutun tamamlanma süreleri
        first_instr = self.instruction_history[0]
        last_instr = self.instruction_history[-1]
        
        # Throughput (birim zamanda tamamlanan iş sayısı)
        pipelined_throughput = len(self.instruction_history) / last_instr.pipelined_end_cycle
        single_cycle_throughput = len(self.instruction_history) / last_instr.single_cycle_end_cycle
        
        # Toplam süre
        total_pipelined = last_instr.pipelined_end_cycle
        total_single_cycle = last_instr.single_cycle_end_cycle
        
        # Ortalama hızlanma oranı
        avg_speedup = avg_single_cycle / avg_pipelined
        
        # Özet metni
        summary = (
            f"<b>Performans Özeti:</b><br><br>"
            f"<b>Toplam Araç Sayısı:</b> {len(self.instruction_history)}<br>"
            f"<b>Boru Hatlı İşlemci Toplam Süre:</b> {total_pipelined} döngü<br>"
            f"<b>Tek Vuruşlu İşlemci Toplam Süre:</b> {total_single_cycle} döngü<br>"
            f"<b>Ortalama Hızlanma Oranı:</b> {avg_speedup:.2f}x<br><br>"
            f"<b>Boru Hatlı Verimlilik (Throughput):</b> {pipelined_throughput:.4f} araç/döngü<br>"
            f"<b>Tek Vuruşlu Verimlilik (Throughput):</b> {single_cycle_throughput:.4f} araç/döngü<br><br>"
            f"<b>Teorik Açıklama:</b><br>"
            f"Boru hatlı (pipelined) işlemci, komutları (araç üretim aşamalarını) bir montaj hattı gibi düşünerek, farklı aşamalardaki komutları eş zamanlı olarak işler. "
            f"Bu sayede, tek bir komutun tamamlanma süresi (gecikme/latency) azalmasa da, birim zamanda tamamlanan komut sayısı (verim/throughput) önemli ölçüde artar.<br>"
            f"<b>- Gecikme (Latency):</b> Bir aracın üretim hattına girmesinden çıkmasına kadar geçen toplam süredir.<br>"
            f"<b>- Verim (Throughput):</b> Birim zamanda üretim hattından çıkan araç sayısıdır.<br>"
            f"<b>- Komut Başına Döngü (CPI - Cycles Per Instruction):</b><br>"
            f"  - <b>Tek Vuruşlu:</b> Her bir komut, tüm {len(STAGES)} aşamayı tamamlayana kadar işlemciyi meşgul eder. Bu nedenle CPI, aşama sayısına eşittir (CPI = {len(STAGES)}).<br>"
            f"  - <b>Boru Hatlı:</b> İlk komut {len(STAGES)} döngüde tamamlandıktan sonra (boru hattının dolması), ideal durumda her döngüde bir yeni komut tamamlanır. Bu da uzun vadede CPI değerini 1'e yaklaştırır.<br>"
            f"<b>Not:</b> Bu simülasyon, boru hattı tehlikeleri (data hazards, control hazards, structural hazards) gibi performans düşürücü faktörleri içermeyen ideal bir durumu modellemektedir. "
            f"Gerçek dünya uygulamalarında bu tehlikeler performansı etkileyebilir."
        )
        
        self.summary_label.setText(summary)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PipelineSimulator()
    window.show()
    sys.exit(app.exec())