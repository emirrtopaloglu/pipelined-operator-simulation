import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QListWidget,
    QLineEdit, QPushButton, QSpinBox, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush
from collections import deque

class Instruction:
    def __init__(self, chassis_no, stage_names):
        self.chassis_no = chassis_no
        self.stage_names = stage_names
        self.color = self.generate_color()  # Her arabaya koyu renk atama
    
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

STAGES = ['Şasi Üretimi', 'Motor ve Aktarma', 'Gövde Montajı', 'İç Aksam', 'Test Sürüşü']
STAGE_SHORT = ['IF', 'ID', 'EX', 'MEM', 'WB']  # Kısa etiketler

class PipelineSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Araba Üretim Simülatörü - Pipeline Görünümü")
        self.setMinimumSize(1000, 600)

        self.pipeline = [None] * len(STAGES)
        self.instruction_queue = deque()
        self.completed = []
        self.cycle = 1
        self.instruction_history = []  # Her talimatın geçmişini sakla
        self.pipeline_history = []     # Her döngüdeki pipeline durumunu sakla

        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulate_cycle)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Giriş alanı
        input_layout = QHBoxLayout()
        self.chassis_input = QLineEdit()
        self.chassis_input.setPlaceholderText("Şasi numaraları (virgülle ayır)")
        input_layout.addWidget(QLabel("Şasi No Gir (Opsiyonel):"))
        input_layout.addWidget(self.chassis_input)

        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(20)
        self.count_input.setValue(5)
        input_layout.addWidget(QLabel("Araba Sayısı:"))
        input_layout.addWidget(self.count_input)

        self.start_button = QPushButton("Başlat")
        self.start_button.clicked.connect(self.start_simulation)
        input_layout.addWidget(self.start_button)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Hız:"))
        self.speed_slider = QSpinBox()
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(1000)
        self.speed_slider.setSingleStep(100)
        self.speed_slider.setSuffix(" ms")
        speed_layout.addWidget(self.speed_slider)
        input_layout.addLayout(speed_layout)

        main_layout.addLayout(input_layout)

        # Ana simülasyon alanı
        simulation_layout = QHBoxLayout()
        
        # Pipeline tablosu - yeniden düzenlendi
        pipeline_layout = QVBoxLayout()
        pipeline_title = QLabel("Pipeline Görünümü")
        pipeline_title.setAlignment(Qt.AlignCenter)
        pipeline_layout.addWidget(pipeline_title)
        
        self.pipeline_table = QTableWidget()
        # Tablo başlangıçta boş olacak, başlatınca sütunlar oluşturulacak
        self.pipeline_table.setRowCount(0)
        self.pipeline_table.setColumnCount(0)
        
        # Tablo ayarları
        self.pipeline_table.verticalHeader().setVisible(True)
        
        pipeline_layout.addWidget(self.pipeline_table)
        simulation_layout.addLayout(pipeline_layout, 3)

        # Üretilen arabalar listesi
        out_layout = QVBoxLayout()
        out_label = QLabel("Üretilen Arabalar 🚘")
        out_label.setAlignment(Qt.AlignCenter)
        out_layout.addWidget(out_label)
        self.output_list = QListWidget()
        out_layout.addWidget(self.output_list)
        simulation_layout.addLayout(out_layout, 1)

        main_layout.addLayout(simulation_layout)

        # Durum etiketi
        self.status_label = QLabel("Simülasyon Bekliyor...")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Renk açıklamaları
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Aşama Kısaltmaları:"))
        for stage, short in zip(STAGES, STAGE_SHORT):
            label = QLabel(f"{short}: {stage}")
            legend_layout.addWidget(label)
            legend_layout.addSpacing(10)
        
        main_layout.addLayout(legend_layout)

    def start_simulation(self):
        # Tüm değişkenleri sıfırla
        self.pipeline = [None] * len(STAGES)
        self.instruction_queue.clear()
        self.completed.clear()
        self.instruction_history = []
        self.pipeline_history = []
        self.cycle = 1
        
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
            self.instruction_history.append(instr)

        # Tabloyu hazırla
        self.pipeline_table.clear()
        self.pipeline_table.setRowCount(0)
        self.pipeline_table.setColumnCount(count)
        
        # Tablo sütun başlıklarını şasi numaraları olarak ayarla
        self.pipeline_table.setHorizontalHeaderLabels([f"Komut #{i+1}\n{instr.chassis_no}" for i, instr in enumerate(self.instruction_history)])
        
        # Sütun genişliklerini ayarla
        header = self.pipeline_table.horizontalHeader()
        for i in range(count):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        self.status_label.setText("🚗 Simülasyon Başladı...")
        
        # Zamanlayıcı hızını ayarla
        self.timer.start(self.speed_slider.value())

    def simulate_cycle(self):
        if not self.instruction_queue and all(x is None for x in self.pipeline):
            self.timer.stop()
            self.status_label.setText("✅ Tüm arabalar üretim hattından çıktı!")
            return

        # Test Sürüşü (WB) aşamasındaki arabayı üretimden çıkar
        if self.pipeline[-1]:
            self.completed.append(self.pipeline[-1])
            self.output_list.addItem(f"🚘 {self.pipeline[-1].chassis_no}")
        
        # Pipeline aşamalarını kaydır
        for i in range(len(STAGES)-1, 0, -1):
            self.pipeline[i] = self.pipeline[i-1]
        
        # Yeni arabayı pipeline'a al
        self.pipeline[0] = self.instruction_queue.popleft() if self.instruction_queue else None
        
        # Durumu güncelle
        self.status_label.setText(f"🔄 Üretim Döngüsü: {self.cycle}")
        
        # Pipeline durumunu kaydet
        current_pipeline = self.pipeline.copy()
        self.pipeline_history.append(current_pipeline)
        
        # Yeni bir satır ekle ve tüm tabloyu güncelle
        self.update_pipeline_table()
        
        self.cycle += 1

    def update_pipeline_table(self):
        # Yeni bir satır ekle
        current_row = self.pipeline_table.rowCount()
        self.pipeline_table.setRowCount(current_row + 1)
        
        # Satır başlığını döngü numarası olarak ayarla
        self.pipeline_table.setVerticalHeaderItem(current_row, QTableWidgetItem(f"Saat Döngüsü {self.cycle}"))
        
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
            elif instruction in self.completed:
                # Bu instruction tamamlandı
                item.setText("✅")
                item.setToolTip(f"{instruction.chassis_no} üretim hattından çıktı")
            else:
                # Bu instruction henüz pipeline'a girmedi
                item.setText("")
                item.setToolTip("Bu araba henüz üretim hattına girmedi")
            
            self.pipeline_table.setItem(current_row, col, item)
        
        # Tabloyu düzenle
        self.pipeline_table.resizeColumnsToContents()
        self.pipeline_table.resizeRowsToContents()
        self.pipeline_table.scrollToBottom()  # En alttaki satırı göster

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PipelineSimulator()
    window.show()
    sys.exit(app.exec())