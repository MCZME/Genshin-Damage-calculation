from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QFont

class DpsPieSelectorWidget(QWidget):
    """带下拉选择框的双饼图组件"""
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._current_data = None  # 存储当前数据
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
            QWidget.DpsPieSelector {
                background: #F8F9FA;
                border-radius: 12px;
                padding: 15px;
            }
            QComboBox {
                min-width: 80px;
                max-width: 150px;
                padding: 4px 8px;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                font-size: 12px;
                color: #495057;
            }
            QComboBox:hover {
                border-color: #ADB5BD;
            }
            QComboBox:focus {
                border-color: #4D9FFF;
                outline: none;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #DEE2E6;
                background: #F8F9FA;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                background: white;
                selection-background-color: #E9ECEF;
                selection-color: #212529;
                outline: none;
                padding: 4px;
            }
        """)
        self.setProperty("class", "DpsPieSelector")
        
        # 创建下拉选择框
        self.combo_box = QComboBox()
        
        # 创建两个饼图组件
        self.element_pie = QChartView()
        self.element_pie.setRenderHint(QPainter.Antialiasing)
        self.element_pie.chart().setTitle("元素伤害分布")
        self.element_pie.chart().setTitleFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        legend = self.element_pie.chart().legend()
        legend.setVisible(True)
        legend.setAlignment(Qt.AlignBottom)
        legend.setFont(QFont("Helvetica Neue", 10))
        legend.setMaximumWidth(200)
        
        self.source_pie = QChartView()
        self.source_pie.setRenderHint(QPainter.Antialiasing)
        self.source_pie.chart().setTitle("伤害来源分布")
        self.source_pie.chart().setTitleFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        legend = self.source_pie.chart().legend()
        legend.setVisible(True)
        legend.setAlignment(Qt.AlignBottom)
        legend.setFont(QFont("Helvetica Neue", 10))  
        legend.setMaximumWidth(200) 
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        layout.addWidget(self.combo_box)
        widget = QWidget()
        chart_layout = QHBoxLayout(widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(0)
        chart_layout.addWidget(self.element_pie)
        chart_layout.addWidget(self.source_pie)
        layout.addWidget(widget)
        
    def _init_empty_chart(self):
        """初始化空饼图"""
        chart = QChart()
        chart.setTitleFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        series = QPieSeries()
        series.append("暂无数据", 1)
        chart.addSeries(series)
        
        self.element_pie.setChart(chart)
        self.source_pie.setChart(chart)

    def set_options(self, options):
        """设置下拉框选项"""
        self.combo_box.clear()
        self.combo_box.addItem("队伍")  # 添加队伍选项
        self.combo_box.addItems(options)
        if options:
            self.combo_box.setCurrentIndex(0)  # 默认选中队伍选项
            self.combo_box.currentIndexChanged.connect(self._update_chart)
            self._update_chart()
        
    def _format_damage(self, damage):
        """格式化伤害值显示"""
        if damage >= 10000:
            return f"{damage/10000:.2f}万"
        return f"{damage:.0f}"

    def set_data(self, data):
        """
        设置饼图数据
        :param data: 字典格式 {'name': {'element': {元素名: 伤害值}, 'type': {伤害类型: 伤害值}}}
        """
        self._current_data = data
        if not data:
            self._init_empty_chart()
            return
            
        # 计算队伍整体数据
        team_data = {
            'element': {},
            'type': {}
        }
        
        for char_data in data.values():
            for element, damage in char_data['element'].items():
                if element not in team_data['element']:
                    team_data['element'][element] = damage
                else:
                    team_data['element'][element] += damage
            
            for type_, damage in char_data['type'].items():
                if type_ not in team_data['type']:
                    team_data['type'][type_] = damage
                else:
                    team_data['type'][type_] += damage
        
        # 添加队伍数据到_current_data
        self._current_data['队伍'] = team_data
            

    def _update_chart(self):
        """当下拉框选择变化时更新图表"""
        if not self._current_data:
            return
            
        name = self.combo_box.currentText()
        if name == "队伍":
            name = "队伍"  # 直接使用队伍数据
        elif name not in self._current_data:
            name = list(self._current_data.keys())[0]

        # 定义颜色列表
        colors = [
            QColor("#FF4D6D"),  # 红色
            QColor("#4D9FFF"),  # 蓝色
            QColor("#2ED8A3"),  # 绿色
            QColor("#FFD166"),  # 黄色
            QColor("#B388FF"),  # 紫色
            QColor("#06D6A0"),  # 青色
            QColor("#EF476F"),  # 粉红
            QColor("#118AB2")   # 深蓝
        ]
        
        # 创建元素伤害饼图
        element_values = []
        for element_dict in self._current_data[name]['element'].values():
            if isinstance(element_dict, dict):
                element_values.extend(element_dict.values())
            else:
                element_values.append(element_dict)
        total_damage = sum(element_values)
        chart = QChart()
        
        series = QPieSeries()
        series.setLabelsVisible(True)
        series.setLabelsPosition(QPieSlice.LabelOutside)
        
        # 添加数据切片
        items = list(self._current_data[name]['element'].items())
        slices = []
        for i, (element, damage) in enumerate(items):
            percentage = (damage / total_damage) * 100
            # 使用HTML换行标签实现强制换行
            label = f"<p align='center'>{element}{self._format_damage(damage)}<br>({percentage:.1f}%)</p>"
            slice = series.append(label, damage)
            slice.setColor(colors[i % len(colors)])
            if percentage >= 1:
                slice.setLabelVisible(True)
            else:
                slice.setLabelVisible(False)
            slices.append((slice, percentage))
        
        chart.addSeries(series)
        self.element_pie.setChart(chart)

        # 创建伤害来源饼图
        total_damage = sum(self._current_data[name]['type'].values())
        chart = QChart()

        series = QPieSeries()
        series.setLabelsVisible(True)
        series.setLabelsPosition(QPieSlice.LabelOutside)
        
        # 添加数据切片
        items = list(self._current_data[name]['type'].items())
        slices = []
        for i, (type_, damage) in enumerate(items):
            percentage = (damage / total_damage) * 100
            # 使用HTML换行标签实现强制换行
            label = f"<p align='center'>{type_}{self._format_damage(damage)}<br>({percentage:.1f}%)</p>"
            slice = series.append(label, damage)
            slice.setColor(colors[i % len(colors)])
            if percentage >= 1:
                slice.setLabelVisible(True)
            else:
                slice.setLabelVisible(False)
        
        chart.addSeries(series)
        self.source_pie.setChart(chart)

class DpsPieWidget(QWidget):
    """角色DPS饼图展示组件"""
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
            QWidget.DpsPie {
                background: #F8F9FA;
                border-radius: 12px;
                padding: 15px;
            }
            QChartView {
                background: transparent;
                border: none;
            }
        """)
        self.setProperty("class", "DpsPie")
        
        # 创建图表视图
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        # 创建图表
        self.dps_selector = DpsPieSelectorWidget()
        
        # 创建布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.chart_view)
        self.main_layout.addWidget(self.dps_selector)
        
        # 初始化空饼图
        self._init_empty_chart()
        
    def _init_empty_chart(self):
        """初始化空饼图"""
        chart = QChart()
        chart.setTitle("角色伤害分布")
        chart.setTitleFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        series = QPieSeries()
        series.append("暂无数据", 1)
        chart.addSeries(series)
        
        self.chart_view.setChart(chart)
        
    def set_data(self, damage_data):
        """
        设置伤害数据
        :param damage_data: 字典格式 {"角色名": 伤害值}
        """
        pie_data = {}
        for damage in [d for d in damage_data.values() if d !=[]]:
            for value in damage:
                c = value['source']
                if c not in pie_data:
                    pie_data[c] = {'value':value['value'],
                                   'data':{'element': {value['element']: value['value']},
                                           'type':{value['type']: value['value']}}}
                else:
                    pie_data[c]['value'] += value['value']
                    if value['element'] not in pie_data[c]['data']['element']:
                        pie_data[c]['data']['element'][value['element']] = value['value']
                    else:
                        pie_data[c]['data']['element'][value['element']] += value['value']
                    if value['type'] not in pie_data[c]['data']['type']:
                        pie_data[c]['data']['type'][value['type']] = value['value']
                    else:
                        pie_data[c]['data']['type'][value['type']] += value['value']
        
        if not pie_data:
            self._init_empty_chart()
            return
        
        self.dps_selector.set_data({k:v['data'] for k,v in pie_data.items()})
        self.dps_selector.set_options([k for k in pie_data.keys()])
            
        chart = QChart()
        chart.setTitle("角色伤害分布")
        chart.setTitleFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        series = QPieSeries()
        series.setLabelsVisible(True)
        series.setLabelsPosition(QPieSlice.LabelOutside)
        
        # 定义颜色列表
        colors = [
            QColor("#FF4D6D"),  # 红色
            QColor("#4D9FFF"),  # 蓝色
            QColor("#2ED8A3"),  # 绿色
            QColor("#FFD166"),  # 黄色
            QColor("#B388FF"),  # 紫色
            QColor("#06D6A0"),  # 青色
            QColor("#EF476F"),  # 粉红
            QColor("#118AB2")   # 深蓝
        ]
        
        # 计算总伤害
        total_damage = sum([v['value'] for v in pie_data.values()])
        
        # 添加数据切片
        items = list({k:v['value'] for k,v in pie_data.items()}.items())
        slices = []
        for i, (character, damage) in enumerate(items):
            percentage = (damage / total_damage) * 100
            slice = series.append(f"{character}\n{damage:.0f}({percentage:.1f}%)", damage)
            slice.setColor(colors[i % len(colors)])
            if percentage >= 1:
                slice.setLabelVisible(True)
            else:
                slice.setLabelVisible(False)
            slices.append((slice, percentage))
            
        # 按百分比排序找出最小的两个切片
        sorted_slices = sorted(slices, key=lambda x: x[1])
        if len(sorted_slices) >= 2:
            smallest1, smallest2 = sorted_slices[0], sorted_slices[1]
            # 如果两个都很小(小于5%)且差距不大(小于1%)
            if (smallest1[1] < 5 and smallest2[1] < 5 and abs(smallest1[1] - smallest2[1]) < 1 and
                smallest1[1] > 1 and smallest2[1] > 1):
                smallest1[0].setLabelArmLengthFactor(0.5)
        
            
        chart.addSeries(series)
        self.chart_view.setChart(chart)
