#!/bin/bash
# 服务器专用补丁 - 使用 akshare 替代新浪 API
# 在服务器上执行此脚本

echo "=========================================="
echo "修复新浪 API 被封禁的问题"
echo "=========================================="

# 创建备份
echo "创建备份..."
cp /opt/iopv/funds/fund_520580.py /opt/iopv/funds/fund_520580.py.bak
cp /opt/iopv/funds/fund_159687.py /opt/iopv/funds/fund_159687.py.bak
cp /opt/iopv/funds/fund_513730.py /opt/iopv/funds/fund_513730.py.bak

# 修改 fund_520580.py
echo "[1/3] 修改 fund_520580.py..."
cat > /tmp/patch_520580.py << 'EOF'
    def _get_market_price(self) -> Optional[dict]:
        """获取市场价格"""
        try:
            import akshare as ak
            
            # 使用 akshare 获取实时行情
            df = ak.fund_etf_spot_em()
            if df is not None and len(df) > 0:
                # 查找对应基金
                fund_data = df[df['代码'] == '520580']
                if len(fund_data) > 0:
                    latest = fund_data.iloc[-1]
                    price = float(latest['最新价'])
                    change_pct = float(latest['涨跌幅'])
                    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return {
                        'price': price,
                        'time': update_time,
                        'change_pct': change_pct
                    }
        except Exception as e:
            print(f"获取市场价格失败: {e}")
        
        return None
EOF

# 修改 fund_159687.py
echo "[2/3] 修改 fund_159687.py..."
cat > /tmp/patch_159687.py << 'EOF'
    def _get_market_price(self) -> Optional[dict]:
        """获取市场价格"""
        try:
            import akshare as ak
            
            # 使用 akshare 获取实时行情
            df = ak.fund_etf_spot_em()
            if df is not None and len(df) > 0:
                # 查找对应基金
                fund_data = df[df['代码'] == '159687']
                if len(fund_data) > 0:
                    latest = fund_data.iloc[-1]
                    price = float(latest['最新价'])
                    change_pct = float(latest['涨跌幅'])
                    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return {
                        'price': price,
                        'time': update_time,
                        'change_pct': change_pct
                    }
        except Exception as e:
            print(f"获取市场价格失败: {e}")
        
        return None
EOF

# 修改 fund_513730.py
echo "[3/3] 修改 fund_513730.py..."
cat > /tmp/patch_513730.py << 'EOF'
    def _get_market_price(self) -> Optional[dict]:
        """获取市场价格"""
        try:
            import akshare as ak
            
            # 使用 akshare 获取实时行情
            df = ak.fund_etf_spot_em()
            if df is not None and len(df) > 0:
                # 查找对应基金
                fund_data = df[df['代码'] == '513730']
                if len(fund_data) > 0:
                    latest = fund_data.iloc[-1]
                    price = float(latest['最新价'])
                    change_pct = float(latest['涨跌幅'])
                    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return {
                        'price': price,
                        'time': update_time,
                        'change_pct': change_pct
                    }
        except Exception as e:
            print(f"获取市场价格失败: {e}")
        
        return None
EOF

echo "=========================================="
echo "补丁文件已创建！"
echo "=========================================="
echo ""
echo "请手动修改以下文件："
echo "  /opt/iopv/funds/fund_520580.py"
echo "  /opt/iopv/funds/fund_159687.py"
echo "  /opt/iopv/funds/fund_513730.py"
echo ""
echo "将 _get_market_price 方法替换为 /tmp/patch_*.py 中的内容"
echo ""
echo "修改完成后重启服务："
echo "  systemctl restart iopv-web"
