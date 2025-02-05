#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
견적서 미리보기 위젯
생성된 견적서를 표시하고 수정할 수 있는 UI 컴포넌트입니다.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QSpinBox, QHeaderView
)
from PySide6.QtCore import Qt

class EstimateViewWidget(QWidget):
    """
    견적서 미리보기 위젯
    AI가 생성한 견적서를 표시하고 수정할 수 있는 인터페이스를 제공합니다.
    """
    
    def __init__(self, parent=None):
        """
        위젯 초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """UI 컴포넌트 초기화 및 레이아웃 설정"""
        main_layout = QVBoxLayout(self)
        
        # 견적 요약 정보
        summary_group = QGroupBox("견적 요약")
        summary_layout = QHBoxLayout()
        
        self.total_cost_label = QLabel("총 견적 금액: 0원")
        self.total_period_label = QLabel("총 소요 기간: 0개월")
        
        summary_layout.addWidget(self.total_cost_label)
        summary_layout.addWidget(self.total_period_label)
        
        summary_group.setLayout(summary_layout)
        
        # 견적 상세 테이블
        self.estimate_table = QTableWidget()
        self.estimate_table.setColumnCount(5)
        self.estimate_table.setHorizontalHeaderLabels([
            "항목", "설명", "단가", "수량", "금액"
        ])
        
        # 테이블 열 너비 설정
        header = self.estimate_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        self.add_row_btn = QPushButton("항목 추가")
        self.remove_row_btn = QPushButton("항목 삭제")
        self.remove_row_btn.setEnabled(False)
        
        button_layout.addWidget(self.add_row_btn)
        button_layout.addWidget(self.remove_row_btn)
        button_layout.addStretch()
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(summary_group)
        main_layout.addWidget(self.estimate_table)
        main_layout.addLayout(button_layout)
        
        # 이벤트 연결
        self.add_row_btn.clicked.connect(self._add_row)
        self.remove_row_btn.clicked.connect(self._remove_selected_rows)
        self.estimate_table.itemSelectionChanged.connect(self._update_remove_button_state)
        self.estimate_table.itemChanged.connect(self._update_total)
        
    def update_estimate(self, estimate_data):
        """
        견적서 데이터로 테이블 업데이트
        
        Args:
            estimate_data (dict): 견적서 데이터
        """
        self.estimate_table.setRowCount(0)
        
        for item in estimate_data["items"]:
            self._add_row(item)
            
        self._update_total()
        
    def get_estimate_data(self):
        """
        현재 테이블의 견적 데이터를 딕셔너리 형태로 반환
        
        Returns:
            dict: 견적서 데이터
        """
        items = []
        for row in range(self.estimate_table.rowCount()):
            item = {
                "item": self.estimate_table.item(row, 0).text(),
                "description": self.estimate_table.item(row, 1).text(),
                "unit_price": int(self.estimate_table.item(row, 2).text().replace(",", "")),
                "quantity": int(self.estimate_table.item(row, 3).text()),
                "amount": int(self.estimate_table.item(row, 4).text().replace(",", ""))
            }
            items.append(item)
            
        return {
            "items": items,
            "total_cost": self._get_total_cost(),
            "total_period": self._get_total_period()
        }
        
    def _add_row(self, item_data=None):
        """
        테이블에 새 행 추가
        
        Args:
            item_data (dict, optional): 추가할 항목 데이터
        """
        row = self.estimate_table.rowCount()
        self.estimate_table.insertRow(row)
        
        if item_data:
            self.estimate_table.setItem(row, 0, QTableWidgetItem(item_data["item"]))
            self.estimate_table.setItem(row, 1, QTableWidgetItem(item_data["description"]))
            self.estimate_table.setItem(row, 2, QTableWidgetItem(f"{item_data['unit_price']:,}"))
            self.estimate_table.setItem(row, 3, QTableWidgetItem(str(item_data["quantity"])))
            self.estimate_table.setItem(row, 4, QTableWidgetItem(f"{item_data['amount']:,}"))
        else:
            for col in range(5):
                self.estimate_table.setItem(row, col, QTableWidgetItem(""))
                
    def _remove_selected_rows(self):
        """선택된 행 삭제"""
        rows = set()
        for item in self.estimate_table.selectedItems():
            rows.add(item.row())
            
        for row in sorted(rows, reverse=True):
            self.estimate_table.removeRow(row)
            
        self._update_total()
        
    def _update_remove_button_state(self):
        """삭제 버튼 활성화 상태 업데이트"""
        self.remove_row_btn.setEnabled(len(self.estimate_table.selectedItems()) > 0)
        
    def _update_total(self):
        """총 견적 금액 및 기간 업데이트"""
        total_cost = self._get_total_cost()
        total_period = self._get_total_period()
        
        self.total_cost_label.setText(f"총 견적 금액: {total_cost:,}원")
        self.total_period_label.setText(f"총 소요 기간: {total_period}개월")
        
    def _get_total_cost(self):
        """총 견적 금액 계산"""
        total = 0
        for row in range(self.estimate_table.rowCount()):
            amount_item = self.estimate_table.item(row, 4)
            if amount_item and amount_item.text():
                total += int(amount_item.text().replace(",", ""))
        return total
        
    def _get_total_period(self):
        """총 소요 기간 계산"""
        # 여기서는 간단히 행 수로 계산
        # 실제로는 더 복잡한 로직이 필요할 수 있음
        return self.estimate_table.rowCount() 