"""
export fakerclaw="mark#new-api-user#cookie"
"""
import requests
import os
import time
import random

retrycount = 1
environ = "fakerclaw"


def send_telegram(message: str):
    bot_token = os.environ.get("TG_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TG_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        print("未配置 Telegram，跳过通知")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code == 200:
            print("Telegram 通知发送成功")
        else:
            print("Telegram 通知失败：", resp.text)
    except Exception as e:
        print("Telegram 发送异常：", e)


def run(arg1, arg2, session):
    headers = {
        "new-api-user": arg1,
        "cookie": arg2,
        "user-agent": "Mozilla/5.0",
        "origin": "https://api.fakerclaw.online",
        "referer": "https://api.fakerclaw.online/console/personal"
    }

    result_lines = []

    for _ in range(retrycount):
        try:
            res = session.post(
                "https://api.fakerclaw.online/api/user/checkin",
                headers=headers,
                json={},
                timeout=20
            ).json()

            msg = res.get("message", "未知结果")
            if "已签到" in msg:
                result_lines.append("签到状态：今日已签")
            elif "签到成功" in msg:
                result_lines.append("签到状态：签到成功")
                quota_awarded = res.get("data", {}).get("quota_awarded", "未知")
                result_lines.append(f"签到奖励：{quota_awarded}")
            else:
                result_lines.append(f"签到返回：{msg}")

            try:
                stats = session.get(
                    "https://api.fakerclaw.online/api/user/checkin",
                    headers=headers,
                    timeout=20
                ).json()
                total = stats.get("data", {}).get("stats", {}).get("total_checkins", "未知")
                result_lines.append(f"累计签到：{total}")
            except Exception:
                pass

            profile = session.get(
                "https://api.fakerclaw.online/api/user/self",
                headers=headers,
                timeout=20
            ).json()

            quota = profile.get("data", {}).get("quota", "未知")
            used_quota = profile.get("data", {}).get("used_quota", 0)
            request_count = profile.get("data", {}).get("request_count", "未知")

            result_lines.append(f"当前可用：{quota}")
            result_lines.append(f"已用额度：{used_quota}")
            result_lines.append(f"请求次数：{request_count}")
            break

        except Exception as e:
            result_lines.append(f"错误：{e}")

    return "\n".join(result_lines)


def main():
    ck = os.environ.get(environ, "")
    if not ck:
        print("请设置变量")
        send_telegram("❌ 签到任务失败：未设置环境变量 fakerclaw")
        return

    ck_list = [x for x in ck.splitlines() if x.strip()]
    all_results = []

    for idx, line in enumerate(ck_list, 1):
        try:
            s = requests.Session()
            mark, a1, a2 = line.split('#', 2)

            print(f"\n===== 账号 {idx}/{len(ck_list)} {mark} =====")
            result = run(a1, a2, s)
            print(result)

            all_results.append(f"<b>账号 {idx}</b>：{mark}\n<pre>{result}</pre>")
            time.sleep(random.randint(1, 2))

        except Exception as e:
            err = f"账号 {idx} 处理失败：{e}"
            print(err)
            all_results.append(f"<b>账号 {idx}</b>\n<pre>{err}</pre>")

    final_msg = "✅ <b>签到任务执行完成</b>\n\n" + "\n\n".join(all_results)
    send_telegram(final_msg)
    print("\n执行完成")


if __name__ == '__main__':
    main()
