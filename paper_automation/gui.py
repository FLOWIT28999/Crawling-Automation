"""
PySide6 GUI 모듈
RISS 학술논문 자동 수집 시스템의 그래픽 사용자 인터페이스
"""

import sys
import json
import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QSpinBox, QCheckBox,
    QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QTabWidget, QComboBox, QSplitter,
    QHeaderView, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSettings
from PySide6.QtGui import QFont, QIcon, QPalette, QColor

from src.backend import PaperCollectorWorker, PaperCollectionEngine

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.config = self.load_config()
        self.settings = QSettings('RISS_Automation', 'MainApp')
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("RISS 학술논문 자동 수집 시스템")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 상단 설정 영역
        settings_widget = self.create_settings_widget()
        main_layout.addWidget(settings_widget)
        
        # 중간 컨트롤 영역
        control_widget = self.create_control_widget()
        main_layout.addWidget(control_widget)
        
        # 하단 결과 영역 (탭)
        self.tab_widget = self.create_result_tabs()
        main_layout.addWidget(self.tab_widget)
        
        # 스타일 적용
        self.apply_styles()
        
    def create_settings_widget(self) -> QWidget:
        """설정 위젯 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 검색 설정 그룹
        search_group = QGroupBox("검색 설정")
        search_layout = QVBoxLayout()
        
        # 키워드 입력
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("검색 키워드:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("예: AI, 머신러닝, 딥러닝 (쉼표로 구분)")
        keyword_layout.addWidget(self.keyword_input)
        search_layout.addLayout(keyword_layout)
        
        # 논문 개수 설정
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("수집할 논문 개수:"))
        self.paper_count_spin = QSpinBox()
        self.paper_count_spin.setRange(1, 500)
        self.paper_count_spin.setValue(50)
        count_layout.addWidget(self.paper_count_spin)
        count_layout.addWidget(QLabel("개"))
        count_layout.addStretch()
        
        # 무료 논문만 체크박스
        self.free_only_check = QCheckBox("무료 논문만 수집")
        self.free_only_check.setChecked(True)
        count_layout.addWidget(self.free_only_check)
        search_layout.addLayout(count_layout)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # API 설정 그룹
        api_group = QGroupBox("API 설정")
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("Gemini API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("API 키를 입력하세요")
        api_layout.addWidget(self.api_key_input)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 출력 설정 그룹
        output_group = QGroupBox("출력 설정")
        output_layout = QVBoxLayout()
        
        # 저장 경로
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("저장 경로:"))
        self.output_path_input = QLineEdit()
        self.output_path_input.setText("./results")
        path_layout.addWidget(self.output_path_input)
        self.browse_button = QPushButton("찾아보기")
        self.browse_button.clicked.connect(self.browse_output_path)
        path_layout.addWidget(self.browse_button)
        output_layout.addLayout(path_layout)
        
        # 출력 형식
        format_layout = QHBoxLayout()
        self.json_check = QCheckBox("JSON 저장")
        self.json_check.setChecked(True)
        self.excel_check = QCheckBox("Excel 저장")
        self.excel_check.setChecked(True)
        format_layout.addWidget(self.json_check)
        format_layout.addWidget(self.excel_check)
        format_layout.addStretch()
        output_layout.addLayout(format_layout)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        return widget
        
    def create_control_widget(self) -> QWidget:
        """컨트롤 위젯 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("시작")
        self.start_button.clicked.connect(self.start_collection)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_collection)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.stop_button)
        
        self.save_settings_button = QPushButton("설정 저장")
        self.save_settings_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_settings_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 진행 상황 그룹
        progress_group = QGroupBox("진행 상황")
        progress_layout = QVBoxLayout()
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        # 상태 메시지
        self.status_label = QLabel("대기 중...")
        progress_layout.addWidget(self.status_label)
        
        # 로그 텍스트
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        return widget
        
    def create_result_tabs(self) -> QTabWidget:
        """결과 탭 위젯 생성"""
        tabs = QTabWidget()
        
        # 결과 미리보기 탭
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels([
            "제목", "저자", "연도", "학술지", "초록", "AI 요약"
        ])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        tabs.addTab(self.result_table, "수집된 논문")
        
        # 통계 탭
        self.stats_widget = QWidget()
        stats_layout = QVBoxLayout(self.stats_widget)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        tabs.addTab(self.stats_widget, "통계")
        
        # 파일 목록 탭
        self.files_list = QListWidget()
        self.files_list.itemDoubleClicked.connect(self.open_file)
        tabs.addTab(self.files_list, "생성된 파일")
        
        return tabs
        
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                background-color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
    def load_config(self) -> dict:
        """설정 파일 로드"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
            
    def save_config(self):
        """현재 설정을 파일에 저장"""
        self.config['search_keywords'] = [k.strip() for k in self.keyword_input.text().split(',')]
        self.config['max_papers'] = self.paper_count_spin.value()
        self.config['free_papers_only'] = self.free_only_check.isChecked()
        self.config['gemini_api_key'] = self.api_key_input.text()
        self.config['output_path'] = self.output_path_input.text()
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
            
    def load_settings(self):
        """저장된 설정 불러오기"""
        keywords = self.settings.value('keywords', '')
        if keywords:
            self.keyword_input.setText(keywords)
            
        paper_count = self.settings.value('paper_count', 50)
        self.paper_count_spin.setValue(int(paper_count))
        
        output_path = self.settings.value('output_path', './results')
        self.output_path_input.setText(output_path)
        
        api_key = self.settings.value('api_key', '')
        if api_key:
            self.api_key_input.setText(api_key)
            
    def save_settings(self):
        """설정 저장"""
        self.settings.setValue('keywords', self.keyword_input.text())
        self.settings.setValue('paper_count', self.paper_count_spin.value())
        self.settings.setValue('output_path', self.output_path_input.text())
        
        if self.api_key_input.text():
            reply = QMessageBox.question(
                self, '확인', 
                'API 키도 저장하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.settings.setValue('api_key', self.api_key_input.text())
                
        QMessageBox.information(self, '알림', '설정이 저장되었습니다.')
        
    def browse_output_path(self):
        """출력 경로 선택"""
        path = QFileDialog.getExistingDirectory(self, "출력 경로 선택")
        if path:
            self.output_path_input.setText(path)
            
    @Slot()
    def start_collection(self):
        """논문 수집 시작"""
        # 입력 검증
        if not self.keyword_input.text():
            QMessageBox.warning(self, '경고', '검색 키워드를 입력해주세요.')
            return
            
        # 설정 업데이트
        self.save_config()
        
        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.result_table.setRowCount(0)
        
        # 워커 스레드 생성 및 시작
        self.worker = PaperCollectorWorker(self.config)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.status.connect(self.update_status)
        self.worker.signals.error.connect(self.handle_error)
        self.worker.signals.finished.connect(self.collection_finished)
        self.worker.signals.result.connect(self.handle_result)
        self.worker.start()
        
        self.log_message("논문 수집을 시작합니다...")
        
    @Slot()
    def stop_collection(self):
        """논문 수집 중지"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_message("논문 수집이 중지되었습니다.")
        
    @Slot(int)
    def update_progress(self, value):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        
    @Slot(str)
    def update_status(self, message):
        """상태 메시지 업데이트"""
        self.status_label.setText(message)
        self.log_message(message)
        
    @Slot(str)
    def handle_error(self, error_message):
        """에러 처리"""
        self.log_message(f"오류: {error_message}")
        QMessageBox.critical(self, '오류', error_message)
        
    @Slot()
    def collection_finished(self):
        """수집 완료"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_message("논문 수집이 완료되었습니다.")
        
    @Slot(object)
    def handle_result(self, result):
        """결과 처리"""
        if result.get('success'):
            # 결과 테이블 업데이트
            papers = result.get('papers', [])
            self.update_result_table(papers)
            
            # 통계 업데이트
            stats = result.get('statistics', {})
            self.update_statistics(stats)
            
            # 파일 목록 업데이트
            files = result.get('files', {})
            self.update_file_list(files)
            
            QMessageBox.information(
                self, '완료', 
                f"총 {len(papers)}개의 논문을 수집했습니다."
            )
        else:
            error = result.get('error', '알 수 없는 오류')
            QMessageBox.warning(self, '실패', f"수집 실패: {error}")
            
    def update_result_table(self, papers):
        """결과 테이블 업데이트"""
        self.result_table.setRowCount(len(papers))
        
        for i, paper in enumerate(papers):
            self.result_table.setItem(i, 0, QTableWidgetItem(paper.get('title', '')))
            self.result_table.setItem(i, 1, QTableWidgetItem(paper.get('authors', '')))
            self.result_table.setItem(i, 2, QTableWidgetItem(paper.get('year', '')))
            self.result_table.setItem(i, 3, QTableWidgetItem(paper.get('journal', '')))
            
            abstract = paper.get('abstract', '')[:100] + '...' if len(paper.get('abstract', '')) > 100 else paper.get('abstract', '')
            self.result_table.setItem(i, 4, QTableWidgetItem(abstract))
            
            summary = paper.get('summary', '')[:100] + '...' if len(paper.get('summary', '')) > 100 else paper.get('summary', '')
            self.result_table.setItem(i, 5, QTableWidgetItem(summary))
            
        self.result_table.resizeColumnsToContents()
        
    def update_statistics(self, stats):
        """통계 업데이트"""
        stats_text = "=== 수집 통계 ===\n\n"
        stats_text += f"총 논문 수: {stats.get('total', 0)}\n"
        stats_text += f"초록 있는 논문: {stats.get('has_abstract', 0)}\n"
        stats_text += f"원문 링크 있는 논문: {stats.get('has_fulltext', 0)}\n"
        stats_text += f"키워드 있는 논문: {stats.get('has_keywords', 0)}\n\n"
        
        years = stats.get('years', {})
        if years:
            stats_text += "=== 연도별 분포 ===\n"
            for year, count in sorted(years.items()):
                stats_text += f"{year}: {count}개\n"
                
        self.stats_text.setText(stats_text)
        
    def update_file_list(self, files):
        """파일 목록 업데이트"""
        self.files_list.clear()
        
        for file_type, filepath in files.items():
            item = QListWidgetItem(f"[{file_type.upper()}] {filepath}")
            item.setData(Qt.UserRole, filepath)
            self.files_list.addItem(item)
            
    def open_file(self, item):
        """파일 열기"""
        filepath = item.data(Qt.UserRole)
        if filepath and os.path.exists(filepath):
            os.startfile(filepath) if sys.platform == 'win32' else os.system(f'open "{filepath}"')
            
    def log_message(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        """프로그램 종료 시"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, '확인',
                '작업이 진행 중입니다. 종료하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()