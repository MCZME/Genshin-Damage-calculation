from nicegui import ui

class GenshinTheme:
    """
    MD3 + Genshin 融合主题引擎
    负责管理动态色彩令牌、磨砂玻璃材质和全局样式注入
    """
    
    # 基础色彩令牌 (Global Tokens)
    SURFACE = "#0B0E18"
    ON_SURFACE = "#ECE5D8"
    SURFACE_VARIANT = "rgba(30, 41, 59, 0.7)"
    
    # 动态元素色池
    ELEMENTS = {
        'Pyro':   {'primary': '#FF5C5C', 'container': '#4A1B1B'},
        'Hydro':  {'primary': '#4FB7FF', 'container': '#1B324A'},
        'Dendro': {'primary': '#A5C83B', 'container': '#2D3815'},
        'Electro':{'primary': '#B283FF', 'container': '#321B4A'},
        'Anemo':  {'primary': '#72E2C3', 'container': '#1B4A3E'},
        'Cryo':   {'primary': '#A0E9FF', 'container': '#1B3E4A'},
        'Geo':    {'primary': '#FFE070', 'container': '#4A3E1B'},
        'Neutral':{'primary': '#94A3B8', 'container': '#1E293B'}
    }

    @staticmethod
    def apply():
        """注入全局 CSS 变量与材质样式"""
        ui.add_head_html(f'''
            <style>
                :root {{
                    --md-surface: {GenshinTheme.SURFACE};
                    --md-on-surface: {GenshinTheme.ON_SURFACE};
                    --md-primary: {GenshinTheme.ELEMENTS['Neutral']['primary']};
                    --md-primary-container: {GenshinTheme.ELEMENTS['Neutral']['container']};
                }}
                
                body {{
                    background-color: var(--md-surface) !important;
                    color: var(--md-on-surface) !important;
                    font-family: 'Inter', system-ui, -apple-system, sans-serif;
                    -webkit-font-smoothing: antialiased;
                    margin: 0;
                }}

                /* MD3 + Genshin 材质系统 - 面板化 (Panes) */
                .genshin-glass {{
                    background: rgba(15, 23, 42, 0.6);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                }}
                
                .genshin-pane {{
                    border-radius: 28px;
                    transition: all 0.4s cubic-bezier(0.1, 0.7, 0.1, 1);
                }}
                
                .genshin-card:hover {{
                    border-color: var(--md-primary);
                    background: rgba(255, 255, 255, 0.05);
                }}

                /* MD3 状态反馈 (Ripple 模拟) */
                .q-ripple {{
                    color: var(--md-primary) !important;
                }}

                /* 隐藏 NiceGUI 默认内间距 */
                .nicegui-content {{
                    padding: 0 !important;
                }}
                
                /* 自定义输入框样式 (MD3 Outlined) */
                .q-field--outlined .q-field__control:before {{
                    border: 1px solid rgba(255, 255, 255, 0.2) !important;
                }}
                .q-field--focused .q-field__control:after {{
                    border-color: var(--md-primary) !important;
                }}
            </style>
        ''')

    @staticmethod
    def set_element(element: str):
        """动态更新当前 UI 的元素主题色"""
        theme = GenshinTheme.ELEMENTS.get(element, GenshinTheme.ELEMENTS['Neutral'])
        ui.run_javascript(f'''
            document.documentElement.style.setProperty('--md-primary', '{theme['primary']}');
            document.documentElement.style.setProperty('--md-primary-container', '{theme['container']}');
        ''')
