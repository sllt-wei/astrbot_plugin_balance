import requests
import json
from datetime import datetime
from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import AstrBotConfig
from astrbot.api.star import Context, Star, register

# 硅基流动余额查询
def query_siliconflow_balance(api_key):
    url = "https://api.siliconflow.cn/v1/user/info"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('status') and data.get('data'):
            balance_info = data['data']
            result = (
                f"硅基流动账户余额信息:\n"
                f"用户ID: {balance_info['id']}\n"
                f"用户名: {balance_info['name']}\n"
                f"邮箱: {balance_info['email']}\n"
                f"余额(美元): {balance_info['balance']}\n"
                f"充值余额(美元): {balance_info['chargeBalance']}\n"
                f"总余额(美元): {balance_info['totalBalance']}\n"
            )
            return result
        else:
            return "获取硅基流动余额失败：" + data.get('message', '未知错误')
    except requests.exceptions.RequestException as e:
        return f"请求错误: {e}"

# OpenAI余额查询
def query_openai_balance(api_key):
    base_url = "https://api.openai.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # 获取今天的日期（格式：YYYY-MM-DD）
        today = datetime.today().strftime('%Y-%m-%d')

        subscription_url = f"{base_url}/v1/dashboard/billing/subscription"
        subscription_response = requests.get(subscription_url, headers=headers)
        subscription_response.raise_for_status()
        subscription_data = subscription_response.json()

        usage_url = f"{base_url}/v1/dashboard/billing/usage?start_date={today}&end_date={today}"
        usage_response = requests.get(usage_url, headers=headers)
        usage_response.raise_for_status()
        usage_data = usage_response.json()

        account_balance = subscription_data[0].get("soft_limit_usd", 0)
        used_balance = usage_data.get("total_usage", 0) / 100
        remaining_balance = account_balance - used_balance

        result = (
            f"OpenAI账户余额信息:\n"
            f"是否已绑定支付方式: {'是' if subscription_data[0].get('has_payment_method') else '否'}\n"
            f"账户额度(美元): {account_balance:.2f}\n"
            f"已使用额度(美元): {used_balance:.2f}\n"
            f"剩余额度(美元): {remaining_balance:.2f}\n"
            f"API访问权限截止时间: {subscription_data[0].get('access_until', '无限制')}\n"
        )
        return result
    except requests.exceptions.RequestException as e:
        return f"请求错误: {e}"

# 定义查询IP地址信息的API URL
IP_API_URL = "http://ip-api.com/json/"

# 注册插件的装饰器
@register(
    "综合查询",
    "API余额查询与IP查询", 
    "支持硅基流动与OpenAI余额查询及IP查询功能", 
    "1.0.0", 
    "https://github.com/Chris95743/astrbot_plugin_balance"
)
class PluginBalanceIP(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    # 查询硅基余额命令
    @filter.command("硅基余额")
    async def siliconflow_balance(self, event: AstrMessageEvent):
        """查询硅基流动余额"""
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入API密钥，格式为：硅基余额 <你的API密钥>")
            return

        # 处理消息中的 At 对象，提取文本
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        if not message_text:
            yield event.plain_result("请输入API密钥，格式为：硅基余额 <你的API密钥>")
            return

        api_key = message_text.split()[1].strip()
        result = query_siliconflow_balance(api_key)
        yield event.plain_result(result)

    # 查询GPT余额命令
    @filter.command("GPT余额")
    async def openai_balance(self, event: AstrMessageEvent):
        """查询OpenAI余额"""
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入API密钥，格式为：GPT余额 <你的API密钥>")
            return

        # 处理消息中的 At 对象，提取文本
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        if not message_text:
            yield event.plain_result("请输入API密钥，格式为：GPT余额 <你的API密钥>")
            return

        api_key = message_text.split()[1].strip()
        result = query_openai_balance(api_key)
        yield event.plain_result(result)

    # 查询IP命令
    @filter.command("查询IP")
    async def query_ip_info(self, event: AstrMessageEvent):
        """查询指定IP地址的归属地和运营商"""
        messages = event.get_messages()

        if not messages:
            yield event.plain_result("请输入IP地址，格式为：查询IP <IP地址>")
            return

        # 处理消息中的 At 对象，提取文本
        message_text = ""
        for message in messages:
            if isinstance(message, At):
                continue  # 跳过 At 类型的消息
            message_text = message.text
            break  # 获取第一个非 At 消息

        if not message_text:
            yield event.plain_result("请输入IP地址，格式为：查询IP <IP地址>")
            return

        ip_address = message_text.split()[1].strip()
        try:
            # 使用ip-api获取IP信息
            response = requests.get(f"{IP_API_URL}{ip_address}")
            data = response.json()

            # 检查API响应
            if data['status'] == 'fail':
                yield event.plain_result(f"无法查询IP地址 {ip_address} 的信息，请检查IP地址是否有效。")
                return

            # 提取信息
            country = data.get('country', '未知')
            region = data.get('regionName', '未知')
            city = data.get('city', '未知')
            zip_code = data.get('zip', '未知')
            isp = data.get('isp', '未知')
            org = data.get('org', '未知')
            asn = data.get('as', '未知')
            lat = data.get('lat', '未知')
            lon = data.get('lon', '未知')
            query_ip = data.get('query', '未知')

            # 返回查询结果（中文翻译）
            result = (
                f"IP 地址: {query_ip}\n"
                f"归属地: {country} {region} {city}\n"
                f"邮政编码: {zip_code}\n"
                f"运营商: {isp}\n"
                f"组织: {org}\n"
                f"ASN（自治系统号）: {asn}\n"
                f"经度: {lon}\n"
                f"纬度: {lat}"
            )
            yield event.plain_result(result)

        except requests.RequestException as e:
            yield event.plain_result(f"查询IP信息时发生错误: {str(e)}")

    # 查询帮助命令
    @filter.command("查询帮助")
    async def query_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = (
            "使用方法：\n"
            "/硅基余额 <API密钥>: 查询硅基流动平台的余额\n"
            "/GPT余额 <API密钥>: 查询OpenAI平台的余额\n"
            "/查询IP <IP地址/域名>: 查询指定IP地址的归属地和运营商信息\n"
            "/查询帮助: 显示命令的帮助信息\n"
        )
        yield event.plain_result(help_text)
