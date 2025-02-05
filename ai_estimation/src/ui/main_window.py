"""
메인 윈도우 모듈
애플리케이션의 메인 윈도우 UI를 구현합니다.
"""

import os
import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QMessageBox, QFileDialog,
    QProgressDialog
)
from PySide6.QtCore import Qt, Slot, QTimer
from src.config.constants import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, ERROR_MESSAGES
from src.ui.project_input_widget import ProjectInputWidget
from src.ui.estimate_view_widget import EstimateViewWidget
from src.services.estimate_service import EstimateService
from src.database.db_manager import DatabaseManager
from src.utils.excel_handler import ExcelHandler

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""

    def __init__(self):
        """메인 윈도우 초기화"""
        super().__init__()
        
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 서비스 및 매니저 초기화
        self.estimate_service = EstimateService()
        self.db_manager = DatabaseManager()
        self.excel_handler = ExcelHandler()
        
        # 현재 프로젝트 데이터
        self.current_project: Optional[Dict[str, Any]] = None
        
        # 로딩 다이얼로그 초기화
        self.progress_dialog = None
        
        # UI 초기화
        self._init_ui()
        
    def _init_ui(self):
        """UI 컴포넌트 초기화"""
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(central_widget)
        
        # 좌측 패널 (프로젝트 정보 입력)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 프로젝트 입력 위젯
        self.project_input = ProjectInputWidget()
        left_layout.addWidget(self.project_input)
        
        # 견적 생성 버튼
        self.generate_button = QPushButton("견적 생성")
        self.generate_button.clicked.connect(self._generate_estimate)
        left_layout.addWidget(self.generate_button)
        
        main_layout.addWidget(left_panel)
        
        # 우측 패널 (견적서 표시)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 견적서 표시 위젯
        self.estimate_view = EstimateViewWidget()
        right_layout.addWidget(self.estimate_view)
        
        # 하단 버튼 그룹
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self._save_project)
        button_layout.addWidget(self.save_button)
        
        self.export_button = QPushButton("엑셀로 내보내기")
        self.export_button.clicked.connect(self._export_to_excel)
        button_layout.addWidget(self.export_button)
        
        right_layout.addLayout(button_layout)
        main_layout.addWidget(right_panel)
        
        # 상태바 설정
        self.statusBar().showMessage("준비")
        
        # 버튼 초기 상태 설정
        self._update_button_states(False)

    def _update_button_states(self, has_estimate: bool):
        """버튼 상태를 업데이트합니다."""
        self.save_button.setEnabled(has_estimate)
        self.export_button.setEnabled(has_estimate)

    def _show_loading(self, message: str):
        """로딩 다이얼로그를 표시합니다."""
        self.progress_dialog = QProgressDialog(message, None, 0, 0, self)
        self.progress_dialog.setWindowTitle("처리 중...")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()
        
        # 프로그레스 바 애니메이션
        self.progress_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(100)

    def _hide_loading(self):
        """로딩 다이얼로그를 숨깁니다."""
        if self.progress_dialog:
            self.timer.stop()
            self.progress_dialog.close()
            self.progress_dialog = None

    def _update_progress(self):
        """프로그레스 바를 업데이트합니다."""
        if self.progress_dialog:
            self.progress_value = (self.progress_value + 1) % 100
            self.progress_dialog.setValue(self.progress_value)

    @Slot()
    def _generate_estimate(self):
        """견적 생성"""
        try:
            # 버튼 비활성화
            self.generate_button.setEnabled(False)
            
            # 프로젝트 정보 가져오기
            project_info = self.project_input.get_project_info()
            
            # 로딩 표시
            self._show_loading("견적을 생성하고 있습니다...")
            
            # 견적 생성 (QTimer를 사용하여 비동기적으로 처리)
            QTimer.singleShot(100, lambda: self._process_estimate(project_info))
            
        except Exception as e:
            self._hide_loading()
            self.generate_button.setEnabled(True)
            logger.error(f"견적 생성 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", str(e))

    def _process_estimate(self, project_info: Dict[str, Any]):
        """견적을 생성하고 결과를 처리합니다."""
        try:
            # 견적 생성
            self.current_project = {
                'info': project_info,
                'estimate': self.estimate_service.generate_estimate(project_info)
            }
            
            # 견적 표시
            self.estimate_view.display_estimate(self.current_project['estimate'])
            
            # 버튼 상태 업데이트
            self._update_button_states(True)
            
            # 상태 메시지 업데이트
            self.statusBar().showMessage("견적이 생성되었습니다.")
            
        except Exception as e:
            logger.error(f"견적 생성 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", str(e))
            
        finally:
            # 로딩 숨기기
            self._hide_loading()
            # 버튼 활성화
            self.generate_button.setEnabled(True)

    @Slot()
    def _save_project(self):
        """프로젝트 저장"""
        try:
            if not self.current_project:
                raise Exception("저장할 프로젝트가 없습니다.")
                
            # 데이터베이스에 저장
            project_id = self.db_manager.save_project(
                self.current_project['info']['name'],
                self.current_project
            )
            
            self.statusBar().showMessage(f"프로젝트가 저장되었습니다. (ID: {project_id})")
            
        except Exception as e:
            logger.error(f"프로젝트 저장 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", str(e))

    @Slot()
    def _export_to_excel(self):
        """엑셀 파일로 내보내기"""
        try:
            if not self.current_project:
                raise Exception("내보낼 견적이 없습니다.")
                
            # 파일 저장 다이얼로그
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "견적서 저장",
                os.path.join(os.path.expanduser("~"), "견적서.xlsx"),
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                # 로딩 표시
                self._show_loading("엑셀 파일을 생성하고 있습니다...")
                
                # 엑셀 파일로 내보내기 (QTimer를 사용하여 비동기적으로 처리)
                QTimer.singleShot(100, lambda: self._process_excel_export(file_path))
                
        except Exception as e:
            logger.error(f"엑셀 내보내기 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", str(e))

    def _process_excel_export(self, file_path: str):
        """엑셀 파일 내보내기를 처리합니다."""
        try:
            # 엑셀 파일로 내보내기
            self.excel_handler.export_estimate(
                self.current_project['estimate'],
                file_path
            )
            
            self.statusBar().showMessage(f"견적서가 저장되었습니다: {file_path}")
            
        except Exception as e:
            logger.error(f"엑셀 내보내기 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", str(e))
            
        finally:
            # 로딩 숨기기
            self._hide_loading()

    def closeEvent(self, event):
        """프로그램 종료 시 처리"""
        reply = QMessageBox.question(
            self,
            '종료 확인',
            '프로그램을 종료하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore() 