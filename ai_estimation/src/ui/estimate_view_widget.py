"""
견적서 표시 위젯 모듈
생성된 견적서를 표시하고 수정할 수 있는 UI를 구현합니다.
"""

import logging
from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QPushButton, QHBoxLayout,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from src.config.constants import ERROR_MESSAGES

logger = logging.getLogger(__name__)

class EstimateViewWidget(QWidget):
    """견적서 표시 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 인건비 테이블
        labor_label = QLabel("인건비")
        labor_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(labor_label)
        
        self.labor_table = QTableWidget()
        self.labor_table.setColumnCount(4)
        self.labor_table.setHorizontalHeaderLabels(['역할', '단가(월)', '투입기간(월)', '금액'])
        self.labor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.labor_table)
        
        # 기타 비용 테이블
        other_label = QLabel("기타 비용")
        other_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(other_label)
        
        self.other_table = QTableWidget()
        self.other_table.setColumnCount(3)
        self.other_table.setHorizontalHeaderLabels(['항목', '금액', '비고'])
        self.other_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.other_table)
        
        # 피드백 입력
        feedback_label = QLabel("피드백")
        feedback_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(feedback_label)
        
        self.feedback_edit = QTextEdit()
        self.feedback_edit.setPlaceholderText("견적서에 대한 피드백을 입력하세요")
        self.feedback_edit.setMaximumHeight(100)
        layout.addWidget(self.feedback_edit)
        
        # 피드백 전송 버튼
        button_layout = QHBoxLayout()
        self.submit_feedback_button = QPushButton("피드백 전송")
        self.submit_feedback_button.clicked.connect(self._submit_feedback)
        button_layout.addStretch()
        button_layout.addWidget(self.submit_feedback_button)
        layout.addLayout(button_layout)
        
        # 현재 견적 데이터 저장
        self.current_estimate: Dict[str, Any] = {}
        
    def display_estimate(self, estimate_data: Dict[str, Any]):
        """견적 데이터를 화면에 표시합니다."""
        try:
            self.current_estimate = estimate_data
            
            # 인건비 테이블 업데이트
            self._update_labor_table(estimate_data.get('labor_costs', []))
            
            # 기타 비용 테이블 업데이트
            self._update_other_costs_table(estimate_data)
            
        except Exception as e:
            logger.error(f"견적 표시 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", str(e))
            
    def _update_labor_table(self, labor_costs: List[Dict[str, Any]]):
        """인건비 테이블을 업데이트합니다."""
        self.labor_table.setRowCount(len(labor_costs))
        
        for row, cost in enumerate(labor_costs):
            self.labor_table.setItem(row, 0, QTableWidgetItem(cost['role']))
            self.labor_table.setItem(row, 1, QTableWidgetItem(f"{cost['monthly_rate']:,}"))
            self.labor_table.setItem(row, 2, QTableWidgetItem(str(cost['duration'])))
            self.labor_table.setItem(row, 3, QTableWidgetItem(f"{cost['monthly_rate'] * cost['duration']:,}"))
            
    def _update_other_costs_table(self, estimate_data: Dict[str, Any]):
        """기타 비용 테이블을 업데이트합니다."""
        other_costs = [
            ('개발 환경 구축 비용', estimate_data.get('setup_cost', 0), ''),
            ('라이선스 및 외부 서비스', estimate_data.get('license_cost', 0), ''),
            ('유지보수 비용', estimate_data.get('maintenance_cost', 0), '옵션'),
            ('예비비', estimate_data.get('contingency', 0), '전체 금액의 10%'),
            ('총 견적 금액', estimate_data.get('total_cost', 0), '')
        ]
        
        self.other_table.setRowCount(len(other_costs))
        
        for row, (item, cost, note) in enumerate(other_costs):
            self.other_table.setItem(row, 0, QTableWidgetItem(item))
            self.other_table.setItem(row, 1, QTableWidgetItem(f"{cost:,}"))
            self.other_table.setItem(row, 2, QTableWidgetItem(note))
            
    def _submit_feedback(self):
        """피드백을 전송합니다."""
        feedback = self.feedback_edit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "경고", "피드백을 입력해주세요.")
            return
            
        # 여기서 피드백 처리 로직을 구현합니다.
        # 실제 구현에서는 부모 위젯이나 시그널을 통해 처리할 수 있습니다.
        QMessageBox.information(self, "알림", "피드백이 전송되었습니다.")
        self.feedback_edit.clear()
        
    def clear(self):
        """위젯의 내용을 초기화합니다."""
        self.labor_table.setRowCount(0)
        self.other_table.setRowCount(0)
        self.feedback_edit.clear()
        self.current_estimate = {} 