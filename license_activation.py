import requests
import json
import sys
import platform
import traceback
from generate_device_id import get_device_id

def activate_license(license_key, api_base_url="https://yymwxx.cn"):
    """
    Activates a license by sending the license key and device ID to the backend API.
    
    Args:
        license_key (str): The license key to activate
        api_base_url (str): The base URL of the API server
        
    Returns:
        dict: A dictionary containing activation results with keys:
            - success (bool): Whether activation was successful
            - message (str): A message describing the result
            - user_email (str, optional): The email associated with the license (if successful)
            - product_id (str, optional): The product ID associated with the license (if successful)
    """
    print("="*50)
    print(f"开始激活流程")
    print(f"Python版本: {sys.version}")
    print(f"平台信息: {platform.platform()}")
    print("="*50)
    
    # Strip any whitespace and convert to uppercase for consistency
    license_key = license_key.strip().upper()
    print(f"格式化后的激活码: {license_key}")
    
    # Generate the device ID
    try:
        print("\n正在生成设备ID...")
        device_id = get_device_id()
        print(f"成功获取设备ID: {device_id}")
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"生成设备ID时出错: {e}")
        print(f"错误详情:\n{error_details}")
        return {
            "success": False,
            "message": f"生成设备ID时出错: {str(e)}"
        }
    
    # Prepare the API endpoint and request data
    api_url = f"{api_base_url}/api/activate-license"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "licenseKey": license_key,
        "deviceId": device_id
    }
    
    print("\n准备发送激活请求:")
    print(f"API地址: {api_url}")
    print(f"请求头: {headers}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    # Make the API request
    try:
        print(f"\n正在发送激活请求至 {api_url}...")
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=30)
        print(f"收到响应 - 状态码: {response.status_code}")
        print(f"响应内容 (前200字符): {response.text[:200]}{'...' if len(response.text) > 200 else ''}")

        if response.ok: # 状态码在 200-299 之间
            try:
                result = response.json()
                print(f"解析后的JSON响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get("success"):
                    print("\n激活成功!")
                    return {
                        "success": True,
                        "message": result.get("message", "激活成功！"),
                        "user_email": result.get("userEmail"),
                        "product_id": result.get("productId"),
                        "purchaseDate": result.get("purchaseDate") 
                    }
                else:
                    error_message = result.get("message", f"激活失败 (来自服务器)")
                    print(f"\n激活失败 (业务层面): {error_message}")
                    return {"success": False, "message": error_message}

            except json.JSONDecodeError:
                print(f"无法将成功的响应解析为JSON (状态码: {response.status_code})")
                print(f"原始响应内容: {response.text}")
                return {
                    "success": False,
                    "message": f"服务器响应格式错误 (状态码: {response.status_code}): 无法解析返回数据。"
                }
        else: # HTTP错误状态码 (e.g., 404, 500, 400 from server if not business error)
            error_message_detail = response.text[:150].strip()
            if response.status_code == 404:
                user_friendly_message = f"激活服务API端点未找到 (404)。请确认服务器配置是否正确。"
            elif "DOCTYPE html" in error_message_detail.lower() or "<html" in error_message_detail.lower():
                user_friendly_message = f"服务器返回了非预期的HTML页面 (状态码: {response.status_code})。请检查API服务器日志。"
            else:
                try:
                    error_json = response.json()
                    user_friendly_message = error_json.get("message", f"服务器错误 (状态码: {response.status_code}): {error_message_detail}")
                except json.JSONDecodeError:
                     user_friendly_message = f"服务器错误 (状态码: {response.status_code}): {error_message_detail}"
            
            print(f"\n激活请求失败 (HTTP {response.status_code}): {user_friendly_message}")
            return {
                "success": False,
                "message": user_friendly_message
            }

    except requests.exceptions.Timeout:
        print(f"\n请求超时")
        return {"success": False, "message": "激活请求超时，请检查网络连接后重试。"}
    except requests.exceptions.ConnectionError as e:
        print(f"\n连接错误: {e}")
        return {"success": False, "message": f"无法连接到激活服务器 ({api_url})。请检查网络或服务器地址。"}
    except requests.RequestException as e:
        print(f"\n请求错误: {e}")
        return {"success": False, "message": f"激活请求发生网络错误: {str(e)}"}
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"\n激活过程中发生意外错误: {e}")
        print(f"错误详情:\n{error_details}")
        return {
            "success": False,
            "message": f"激活过程中发生未知本地错误: {str(e)}"
        }

if __name__ == "__main__":
    try:
        # Test the activation function
        print("="*50)
        print("文智搜激活码验证测试脚本")
        print("="*50)
        
        print("\n提示: 此脚本将生成设备ID并尝试验证激活码")
        license_key = input("\n请输入激活码: ")
        
        # You can change this to your actual API base URL
        api_base = input("\n请输入API基础URL (默认为https://yymwxx.cn): ") or "https://yymwxx.cn"
        
        print("\n正在处理激活请求...")
        result = activate_license(license_key, api_base)
        
        print("\n" + "="*50)
        print("激活结果:")
        print(f"成功: {'是' if result['success'] else '否'}")
        print(f"消息: {result['message']}")
        
        if result['success']:
            print(f"用户邮箱: {result.get('user_email', 'N/A')}")
            print(f"产品ID: {result.get('product_id', 'N/A')}")
            print(f"购买日期: {result.get('purchaseDate', 'N/A')}")
        print("="*50)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"\n程序运行时发生错误: {e}")
        print(f"错误详情:\n{error_details}")
    
    input("\n按Enter键退出...") 