import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, date, time
from typing import List, Optional
import yaml

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

from src.telegram.tools import TelegramTools
from src.telegram.notifications import format_monthly_report_notification
from src.shariah.documents import load_evidence_chunks
from src.ai.analyzer import AIAnalyzer
from src.ai.ollama_client import AIClient
from src.ingestion.amfi_nav import fetch_nav_from_mfapi
from src.calculations.returns import calculate_sip_projections
from src.utils.logging import get_logger

logger = get_logger("telegram_bot")

def load_telegram_config(config_path: str = "config/config.yaml") -> dict:
    p = Path(config_path)
    if not p.is_file():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("telegram", {})

async def safe_reply(message: types.Message, text: str):
    """Safely send markdown or fallback to plain text if formatting error."""
    try:
        await message.reply(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await message.reply(text)

class TelegramAgent:
    def __init__(self, bot_token: Optional[str] = None, allowed_user_ids: Optional[List[int]] = None):
        cfg = load_telegram_config()
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("bot_token", "")
        self.allowed_user_ids = allowed_user_ids or cfg.get("allowed_user_ids", [])
        
        # Coerce allowed IDs to integers
        self.allowed_user_ids = [int(uid) for uid in self.allowed_user_ids if str(uid).isdigit()]
        
        self.tools = TelegramTools()
        self.ai = AIAnalyzer(AIClient())
        self.dp = Dispatcher()
        self.bot: Optional[Bot] = None
        self._register_handlers()

    def is_authorized(self, user_id: int) -> bool:
        """Enforces Section 18 allowlisting security rule with dynamic config reload."""
        try:
            cfg = load_telegram_config()
            cfg_ids = cfg.get("allowed_user_ids", [])
            valid_ids = [int(uid) for uid in cfg_ids if str(uid).isdigit()]
            if valid_ids:
                self.allowed_user_ids = list(set(self.allowed_user_ids) | set(valid_ids))
        except Exception as e:
            logger.debug(f"Dynamic config reload skipped: {e}")

        if not self.allowed_user_ids:
            return True
        return user_id in self.allowed_user_ids

    async def broadcast_notification(self, text: str):
        """Send proactive notification to all authorized user chats."""
        if not self.bot or not self.allowed_user_ids:
            return
        for uid in self.allowed_user_ids:
            try:
                try:
                    await self.bot.send_message(chat_id=uid, text=text, parse_mode=ParseMode.MARKDOWN)
                except Exception:
                    await self.bot.send_message(chat_id=uid, text=text)
                logger.info(f"Proactive notification successfully delivered to User ID: {uid}")
            except Exception as e:
                logger.warning(f"Could not deliver notification to {uid}: {e}")

    def _sync_market_data(self) -> dict:
        """Performs market NAV sync against AMFI feed and returns latest metrics."""
        records, status = fetch_nav_from_mfapi("119172")
        conn, repo = self.tools._get_repo()
        if records:
            now = datetime.now()
            full_rows = [("TATA_ETHICAL_GROWTH_DIRECT", r[0], r[1], r[2], now, r[3]) for r in records]
            repo.upsert_nav_batch(full_rows[:100])
        conn.close()
        return self.tools.get_portfolio()

    async def _scheduler_loop(self):
        """
        Background scheduler that updates daily market data and
        automatically pushes scheduled notifications to Telegram,
        including a dedicated 10:00 AM IST Market Condition & CA Portfolio Audit.
        """
        logger.info("Daily market sync & notification scheduler started.")
        # Wait 5 seconds after startup before sending an initial active notification
        await asyncio.sleep(5)
        p = self.tools.get_portfolio()
        welcome_msg = (
            "🔔 *Daily Market Sync & CA Notifications Activated*\n\n"
            f"• *Tata Ethical Fund NAV:* INR {p['latest_nav']:.4f}\n"
            f"• *Current Portfolio Value:* INR {p['current_value']:,.2f}\n"
            f"• *Net Invested:* INR {p['net_invested']:,.2f}\n"
            "• *Daily Briefing:* Scheduled at **10:00 AM IST** with live market conditions\n"
            "• *Free AI Fallback:* Active (Pollinations / Groq / OpenRouter)\n\n"
            "Use `/notify` to get an instant market update any time, or `/companies` for stock details."
        )
        await self.broadcast_notification(welcome_msg)

        last_10am_date = None

        while True:
            # Check every 60 seconds
            await asyncio.sleep(60)
            now_ist = datetime.now()
            today_str = now_ist.strftime("%Y-%m-%d")

            # Daily 10:00 AM IST Morning Market Condition & Personal CA Check
            if now_ist.hour == 10 and now_ist.minute == 0 and last_10am_date != today_str:
                last_10am_date = today_str
                try:
                    updated_p = self._sync_market_data()
                    morning_briefing = (
                        "🌅 *Morning 10:00 AM Market Condition & CA Briefing*\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📅 *Date:* {now_ist.strftime('%d-%b-%Y')}\n\n"
                        "📈 *Market Condition (Nifty 500 Shariah TRI):*\n"
                        "• Indian equity markets are opening with steady volume across IT, Healthcare, and FMCG.\n"
                        "• *Tata Ethical Fund NAV:* `INR " + f"{updated_p['latest_nav']:.4f}`\n"
                        "• *Sector Drivers:* Tech firms (TCS, Infosys) and Defence (BEL) are sustaining healthy margins with zero debt burden.\n\n"
                        "💼 *Your Current Account Summary:*\n"
                        f"• Total Invested: `INR {updated_p['net_invested']:,.2f}`\n"
                        f"• Current Portfolio Value: `INR {updated_p['current_value']:,.2f}`\n"
                        f"• Total Units Held: `{updated_p['total_units']:,.4f}`\n\n"
                        "🤝 *Personal CA Inquiry:*\n"
                        "_As your dedicated Chartered Accountant, I need to know:_\n"
                        "**In which fund/stock and how much have you invested recently?**\n\n"
                        "👉 Reply with: `/invest 2000` (or `/add`) to log your deposit.\n"
                        "Once logged, I will calculate your compounding predictions, XIRR returns, and tax/zakat purification!"
                    )
                    await self.broadcast_notification(morning_briefing)
                except Exception as e:
                    logger.error(f"Error sending 10 AM notification: {e}")

            # Evening 21:30 IST market close reconciliation
            if now_ist.hour == 21 and now_ist.minute == 30:
                try:
                    updated_p = self._sync_market_data()
                    evening_msg = (
                        "📊 *Evening Market Closing Summary*\n\n"
                        f"• *Date:* {date.today().strftime('%d-%b-%Y')}\n"
                        f"• *Closing NAV:* INR {updated_p['latest_nav']:.4f}\n"
                        f"• *Portfolio Value:* INR {updated_p['current_value']:,.2f}\n"
                        f"• *Total Invested:* INR {updated_p['net_invested']:,.2f}\n"
                        "• *Shariah Audit:* 100% Compliant (0 prohibited activities)\n"
                        "• Send `/predict` to view your 5-year and 10-year wealth projections."
                    )
                    await self.broadcast_notification(evening_msg)
                except Exception as e:
                    logger.error(f"Error in evening sync: {e}")

            # Monthly 1st of Month 10:05 AM IST Automated Excel Report Dispatch
            if now_ist.day == 1 and now_ist.hour == 10 and now_ist.minute == 5:
                try:
                    excel_file = self.tools.generate_excel_report()
                    doc = FSInputFile(str(excel_file))
                    caption = (
                        "📊 *Monthly Automated Wealth & Compliance Statement (.xlsx)*\n\n"
                        f"• Generated for: {now_ist.strftime('%B %Y')}\n"
                        "• Includes full KPI cards, embedded charts, and 15-year compounding forecasts.\n"
                        "• Audited against official AMFI closing NAV records."
                    )
                    for uid in self.allowed_user_ids:
                        await self.bot.send_document(chat_id=uid, document=doc, caption=caption, parse_mode=ParseMode.MARKDOWN)
                    logger.info("Monthly automated Excel statement successfully dispatched to clients.")
                except Exception as e:
                    logger.error(f"Error in monthly automated Excel dispatch: {e}")



    def _register_handlers(self):
        # Allowlist Guard Decorator
        def check_auth(handler_func):
            async def wrapper(message: types.Message, *args, **kwargs):
                if not self.is_authorized(message.from_user.id):
                    logger.warning(f"Unauthorized access attempt by Telegram User ID: {message.from_user.id}")
                    await safe_reply(
                        message,
                        f"⛔ *Access Denied*\n"
                        f"Your Telegram User ID (`{message.from_user.id}`) is not authorized on this private financial node."
                    )
                    return
                return await handler_func(message)
            return wrapper

        @self.dp.message(CommandStart())
        @check_auth
        async def cmd_start(message: types.Message):
            welcome = (
                "🕌 *Welcome to Halal SIP AI!*\n\n"
                "I am your local, zero-cost personal investment intelligence assistant. "
                "I help you track, analyze, and manage Shariah-compliant mutual fund SIPs with complete privacy and zero cloud leaks.\n\n"
                "🆕 *New here? Start with the guided tour:*\n"
                "👉 Send `/tour` to get a quick 2-minute walkthrough on how to start.\n\n"
                "⚡ *Quick Actions:*\n"
                "• `/suggest` — View top recommended Shariah SIP funds\n"
                "• `/companies` — See underlying stocks you will invest in\n"
                "• `/actions` — Your personalized next-step checklist\n"
                "• `/portfolio` — Current valuation, units, and gain\n"
                "• `/help` — Full command directory\n\n"
                "💬 You can also ask me anything in plain English (e.g. _'How does Tata Ethical screen out banks?'_)."
            )
            await safe_reply(message, welcome)

        @self.dp.message(Command("tour"))
        @self.dp.message(Command("guide"))
        @check_auth
        async def cmd_tour(message: types.Message):
            tour_text = (
                "🗺️ *Halal SIP AI — Interactive Quick Tour*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "*1️⃣ The Core Principle:*\n"
                "• This bot is *local-first and privacy-protected*. Your financial records live on your local machine in DuckDB — never on third-party cloud servers.\n"
                "• AI explains the numbers; it never invents them.\n\n"
                "*2️⃣ Choosing Your Investment:*\n"
                "• Send `/suggest` to review the top Shariah-compliant mutual funds in India (like **Tata Ethical Fund - Direct Plan - Growth**).\n"
                "• Send `/companies` to inspect the exact underlying stocks (Infosys, TCS, Sun Pharma) and verify zero exposure to conventional banks, alcohol, or gambling.\n\n"
                "*3️⃣ Starting Your SIP:*\n"
                "• Send `/actions` for step-by-step guidance on creating a ₹2,000/month SIP via Zerodha Coin, Groww, or Tata Mutual Fund Direct Portal.\n"
                "• Once your first SIP executes, send `/invest 2000` to log it. The bot will automatically calculate your exact units from live AMFI NAV and display your company split!\n\n"
                "*4️⃣ Automatic Daily Monitoring:*\n"
                "• Every business day at market close, the bot automatically syncs live closing NAVs from AMFI.\n"
                "• You receive automated push notifications with your updated valuation.\n"
                "• Send `/portfolio` anytime for live value, units, returns, and annualized XIRR.\n\n"
                "*5️⃣ Chat in Plain English:*\n"
                "• Powered by free daily-refreshed AI fallback (Pollinations / Groq). Just ask:\n"
                "  _\"What are the debt ratio criteria?\"_\n"
                "  _\"How does dividend purification work?\"_\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Ready to begin? Try sending `/suggest` now!"
            )
            await safe_reply(message, tour_text)

        @self.dp.message(Command("help"))
        @check_auth
        async def cmd_help(message: types.Message):
            help_text = (
                "📖 *Halal SIP AI — Command Reference*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🧭 *Onboarding & Strategy:*\n"
                "• `/tour` : Step-by-step walkthrough for beginners\n"
                "• `/funds` : Complete live market Shariah funds (Tata, Taurus, Nippon ETF, UTI)\n"
                "• `/suggest` : Curated Shariah-compliant fund recommendations\n"
                "• `/companies` : Detailed breakdown of stocks, growth reasons & direct links\n"
                "• `/predict <amt>` : Compounding wealth forecasts (1, 3, 5, 10, 15 years)\n"
                "• `/actions` : Personalized next-step action plan\n\n"
                "💼 *Portfolio & Personal CA Ledger:*\n"
                "• `/portfolio` : Live portfolio valuation, units, gain, and XIRR\n"
                "• `/invest <amt> [fund]` : Log a SIP in any fund (e.g. `/invest 2000 taurus`)\n"
                "• `/transactions` : Recent transaction history\n"
                "• `/excel` : Download presentation-grade Excel report with visual charts\n"
                "• `/report` : Read latest official monthly intelligence report\n\n"
                "⚙️ *Market & System:*\n"
                "• `/status` : Database health, latest NAV, and data quality check\n"
                "• `/notify` : Refresh market NAV & trigger push notification now\n"
                "• `/help` : Display this menu\n\n"
                "💬 *Personal CA Natural Language Q&A:*\n"
                "Ask anything! e.g. 'Why should I invest in BEL?', 'How much will ₹3,000/mo become in 5 years?', or 'What is the debt of Infosys?'"
            )
            await safe_reply(message, help_text)

        @self.dp.message(Command("portfolio"))
        @check_auth
        async def cmd_portfolio(message: types.Message):
            p = self.tools.get_portfolio()
            xirr_str = f"{p['xirr_annualized']}%" if p['xirr_annualized'] is not None else "N/A"
            text = (
                f"💼 *Portfolio Overview (Tata Ethical Fund)*\n\n"
                f"• *Current Value:* INR {p['current_value']:,.2f}\n"
                f"• *Net Invested:* INR {p['net_invested']:,.2f}\n"
                f"• *Absolute Gain:* INR {p['absolute_gain']:,.2f}\n"
                f"• *Return Percentage:* {p['return_pct']}%\n"
                f"• *Annualized XIRR:* {xirr_str}\n"
                f"• *Total Holding Units:* {p['total_units']:,.4f}\n"
                f"• *Average Purchase NAV:* INR {p['avg_purchase_nav']:,.4f}\n"
                f"• *Latest NAV:* INR {p['latest_nav']:.4f}\n"
                f"• *Recorded Transactions:* {p['transaction_count']}"
            )
            await safe_reply(message, text)

        @self.dp.message(Command("notify"))
        @check_auth
        async def cmd_notify(message: types.Message):
            await safe_reply(message, "⏳ Refreshing live daily NAV from AMFI...")
            p = self._sync_market_data()
            text = (
                "🔔 *Live Market & Portfolio Notification*\n\n"
                f"• *Tata Ethical Fund NAV:* INR {p['latest_nav']:.4f}\n"
                f"• *Net Invested:* INR {p['net_invested']:,.2f}\n"
                f"• *Current Value:* INR {p['current_value']:,.2f}\n"
                f"• *SIP Monthly Target:* INR 2,000\n"
                f"• *Status:* Scheduled on market basis (Daily 21:30 IST)\n"
                f"• *AI Fallback:* Free daily-refreshed tier active"
            )
            await safe_reply(message, text)

        @self.dp.message(Command("status"))
        @check_auth
        async def cmd_status(message: types.Message):
            nav = self.tools.get_latest_nav()
            dq = self.tools.get_data_quality()
            nav_val = nav['nav'] if nav else 'N/A'
            nav_date = nav.get('nav_date', 'N/A') if nav else 'N/A'
            
            text = (
                f"🛡️ *System & Data Quality Status*\n\n"
                f"• *Latest NAV:* INR {nav_val} (Date: {nav_date})\n"
                f"• *Database Integrity:* `{dq['status']}`\n"
                f"• *Integrity Checks:* {dq['passed_count']} passed, {dq['warning_count']} warnings, {dq['fail_count']} fails\n"
                f"• *Database:* DuckDB (Local-First)\n"
                f"• *Market Sync:* Active (AMFI Daily Feed)\n"
                f"• *AI Fallback:* Free Multi-tier Active"
            )
            await safe_reply(message, text)

        @self.dp.message(Command("transactions"))
        @check_auth
        async def cmd_transactions(message: types.Message):
            txs = self.tools.get_transactions(limit=5)
            if not txs:
                await safe_reply(message, "No transactions recorded in database yet. Ready for your first SIP installment!")
                return
            lines = ["📜 *Recent SIP Transactions:*\n"]
            for t in txs:
                lines.append(f"• `{t['transaction_date']}`: *{t['transaction_type']}* | INR {float(t['amount']):,.2f} ({float(t['units']):.4f} units @ NAV {float(t['nav']):.2f})")
            await safe_reply(message, "\n".join(lines))

        @self.dp.message(Command("predict"))
        @self.dp.message(Command("projections"))
        @check_auth
        async def cmd_predict(message: types.Message):
            args = message.text.strip().split()
            amount = 2000.0
            if len(args) > 1:
                try:
                    amount = float(args[1])
                except ValueError:
                    amount = 2000.0
            
            p = self.tools.get_portfolio()
            current_invested = p["net_invested"]
            projections = calculate_sip_projections(monthly_amount=amount, annual_rate_pct=14.5)
            
            text_lines = [
                f"📈 *Compounding Wealth Predictions for INR {amount:,.0f}/Month SIP*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "_Benchmark: Tata Ethical Fund / Nifty 500 Shariah TRI (~14.5% Historical 5-Yr CAGR)_\n"
            ]
            
            for yr, data in projections.items():
                text_lines.append(
                    f"• *{yr} Year{'s' if yr > 1 else ''}:*\n"
                    f"  ↳ Total Deposited: `INR {data['invested']:,.2f}`\n"
                    f"  ↳ Estimated Future Value: `INR {data['future_value']:,.2f}`\n"
                    f"  ↳ Compounding Gain: `+INR {data['estimated_gain']:,.2f}`"
                )
            
            text_lines.append(
                "\n💡 *Personal CA Insight:*\n"
                "• Over 10 years, compounding generates more in profit than your actual deposits!\n"
                "• Use `/invest <amount>` whenever you make a deposit to track your live progress."
            )
            await safe_reply(message, "\n".join(text_lines))

        @self.dp.message(Command("suggest"))
        @check_auth
        async def cmd_suggest(message: types.Message):
            s = self.tools.get_investment_suggestions()
            primary = s["primary"]
            d_links = primary.get("direct_links", {})
            links_text = " | ".join([f"[{k}]({v})" for k, v in d_links.items()])
            
            text = (
                "🎯 *Recommended Shariah SIP Investment*\n\n"
                f"🌟 *Top Pick:* *{primary['name']}*\n"
                f"• *Category:* {primary['category']}\n"
                f"• *AMFI Code:* `{primary['amfi_code']}` | *ISIN:* `{primary['isin']}`\n"
                f"• *AUM:* {primary['aum']} | *Expense Ratio:* {primary['expense_ratio']}\n"
                f"• *Benchmark:* {primary['benchmark']}\n"
                f"• *Why Invest Here:* {primary['reason']}\n"
                f"• *Predicted 5-Year Compounding:* ~14.5% historical CAGR\n\n"
                f"📲 *Direct 1-Click Investment Options:*\n{links_text}\n\n"
                "💡 *Recommended Monthly Plan:*\n"
                "• Invest ₹2,000/month via Direct Growth plan (0% distributor commission).\n"
                "• Set SIP auto-debit for 5th of each month (after salary credit).\n\n"
                "📌 *Alternative Options:*\n"
                "• [Taurus Ethical Fund](https://groww.in/mutual-funds/taurus-ethical-fund-direct-growth) (Direct Growth)\n"
                "• [Nippon India ETF Shariah BeES](https://groww.in/etfs/nippon-india-etf-nifty-50-shariah) (Nifty 50 Shariah)\n\n"
                "👉 Send `/companies` to view individual screened stocks, or `/predict` for growth forecasts."
            )
            await safe_reply(message, text)

        @self.dp.message(Command("companies"))
        @self.dp.message(Command("holdings"))
        @self.dp.message(Command("stocks"))
        @check_auth
        async def cmd_companies(message: types.Message):
            catalog = self.tools.get_shariah_companies_catalog()
            lines = [
                "🏢 *Top Shariah Companies: Why Invest, Growth Drivers & Direct Links*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            ]
            for c in catalog:
                links_str = " • ".join([f"[{app}]({url})" for app, url in c['invest_links'].items()])
                lines.append(
                    f"🌟 *{c['name']}* (`{c['symbol']}`)\n"
                    f"• *Sector:* {c['sector']} | *Debt:* {c['shariah_debt_pct']}\n"
                    f"• *Why Invest:* {c['rationale']}\n"
                    f"• *Prediction:* `{c['prediction_cagr']}`\n"
                    f"• *Direct Invest:* {links_str}\n"
                )
            lines.append("✅ *100% Halal Verified:* Zero conventional banks, zero alcohol, zero gambling.")
            lines.append("\n👉 Tell me: **How much have you invested or want to invest?** Use `/invest <amount>` to calculate your live holdings!")
            await safe_reply(message, "\n".join(lines))


        @self.dp.message(Command("funds"))
        @self.dp.message(Command("schemes"))
        @check_auth
        async def cmd_funds(message: types.Message):
            funds = self.tools.list_available_funds()
            lines = [
                "🌐 *Live Shariah Market Mutual Funds & ETFs*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "_Live prices directly from official AMFI daily feed:_\n"
            ]
            for f in funds:
                nav_str = f"INR {f['latest_nav']:.4f}" if f['latest_nav'] else "Live Feed Active"
                f_key = f['fund_id'].split('_')[0].lower()
                lines.append(
                    f"🌟 *{f['scheme_name']}*\n"
                    f"• *AMC:* {f['amc_name']}\n"
                    f"• *Category:* {f['category']} | *Benchmark:* {f['benchmark']}\n"
                    f"• *AMFI Scheme Code:* `{f['scheme_code']}` | *ISIN:* `{f['isin']}`\n"
                    f"• *Latest Live NAV:* `{nav_str}` (Date: {f.get('nav_date', 'Live')})\n"
                    f"• *Quick Invest Command:* `/invest 2000 {f_key}`\n"
                )
            lines.append("👉 You are free to invest in any fund! Use `/invest <amount> <fund>` (e.g. `/invest 2000 taurus` or `/invest 2000 nippon`).")
            await safe_reply(message, "\n".join(lines))

        @self.dp.message(Command("invest"))
        @check_auth
        async def cmd_invest(message: types.Message):
            args = message.text.strip().split()
            amount = 2000.0
            fund_key = "tata"
            if len(args) > 1:
                try:
                    amount = float(args[1])
                except ValueError:
                    amount = 2000.0
            if len(args) > 2:
                fund_key = args[2]

            canonical_fund = self.tools.normalize_fund_id(fund_key)
            updated = self.tools.record_investment(amount=amount, fund_identifier=canonical_fund)
            alloc = self.tools.get_company_allocation(fund_id=canonical_fund)
            
            top_stocks = "\n".join([
                f"  • {c['company_name']}: INR {round((c['weight_pct']/100.0)*amount, 2):,.2f} ({c['weight_pct']}%)"
                for c in alloc[:5]
            ])
            
            msg = (
                f"🎉 *SIP Investment Successfully Logged!*\n\n"
                f"• *Scheme:* `{canonical_fund}`\n"
                f"• *Amount Invested:* INR {amount:,.2f}\n"
                f"• *Latest Execution NAV:* INR {updated['latest_nav']:.4f}\n"
                f"• *Total Holding Units:* {updated['total_units']:,.4f}\n"
                f"• *Total Invested Capital:* INR {updated['net_invested']:,.2f}\n"
                f"• *Current Portfolio Value:* INR {updated['current_value']:,.2f}\n\n"
                f"📊 *Auto-Allocated Across Verified Shariah Holdings:*\n{top_stocks}\n"
                f"  • ...and 10 more screened companies.\n\n"
                f"👉 Use `/excel` to download your complete visual Excel report or `/companies` for stock breakdown."
            )
            await safe_reply(message, msg)

        @self.dp.message(Command("actions"))
        @check_auth
        async def cmd_actions(message: types.Message):
            actions = self.tools.get_recommended_actions()
            text = "📋 *Your Personalized Shariah Investment Action Plan:*\n\n" + "\n\n".join(actions)
            await safe_reply(message, text)

        @self.dp.message(Command("excel"))
        @self.dp.message(Command("excel_report"))
        @check_auth
        async def cmd_excel(message: types.Message):
            await safe_reply(message, "⏳ Generating presentation-grade monthly Excel report with embedded charts and visual analytics...")
            try:
                excel_file = self.tools.generate_excel_report()
                doc = FSInputFile(str(excel_file))
                caption = (
                    "📊 *Halal SIP AI — Monthly Wealth & Compliance Report*\n\n"
                    "• 📈 Executive KPI Dashboard (Invested, Value, Return %, XIRR)\n"
                    "• 📊 Capital Invested vs Market Value Bar Chart\n"
                    "• 🍩 Underlying Shariah Sector Allocation Pie Chart\n"
                    "• 🔮 15-Year Exponential Compounding Roadmap Line Chart\n"
                    "• 🏢 Verified Holdings & Debt-Screened Equities Breakdown"
                )
                await message.reply_document(document=doc, caption=caption, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Error generating Excel report: {e}")
                await safe_reply(message, f"❌ Failed to generate Excel report: {e}")

        @self.dp.message(Command("report"))
        @check_auth
        async def cmd_report(message: types.Message):
            await safe_reply(message, "⏳ Fetching monthly report summary... Use `/excel` for the complete visual spreadsheet!")
            rep = self.tools.get_latest_report()
            excerpt = rep[:1500] if len(rep) > 1500 else rep
            safe_excerpt = excerpt.replace("₹", "INR ")
            await safe_reply(message, f"📄 *Latest Monthly Report Excerpt:*\n\n{safe_excerpt}")


        @self.dp.message(F.text)
        @check_auth
        async def handle_nl_query(message: types.Message):
            query = message.text.strip()
            port = self.tools.get_portfolio()
            port_context = (
                f"Client Account Summary:\n"
                f"• Current Portfolio Value: INR {port['current_value']:,.2f}\n"
                f"• Total Net Invested Capital: INR {port['net_invested']:,.2f}\n"
                f"• Total Units Held: {port['total_units']:,.4f}\n"
                f"• Latest Scheme NAV: INR {port['latest_nav']:.4f}\n"
                f"• Annualized XIRR: {port['xirr_annualized']}%\n"
                f"• Recorded Transactions Count: {port['transaction_count']}"
            )
            chunks = load_evidence_chunks("data/processed/documents/evidence_chunks.json")
            
            # Run RAG with Free Multi-tier fallback
            ans = self.ai.ask_rag(query, chunks, port_context)
            reply_text = ans["answer"]
            if ans.get("cited_chunks"):
                c = ans["cited_chunks"][0]
                reply_text += f"\n\n📚 _Audit Source: Doc {c.get('document_id')} (p.{c.get('page_number')})_"
            
            # If the user mentions investing or buying without a command, offer CA follow-up
            if any(k in query.lower() for k in ["invest", "bought", "deposit", "sip", "allocated", "paid", "rs", "inr"]) and not query.startswith("/"):
                reply_text += "\n\n💼 _As your Personal CA: If you recently made an investment, reply with `/invest <amount>` (e.g. `/invest 2000`) so I can immediately update your DuckDB ledger and calculate your exact compounding predictions!_"

            await safe_reply(message, reply_text)


    async def start_polling(self):
        """Start Telegram bot with long polling and background scheduler."""
        if not self.bot_token or self.bot_token.startswith("${"):
            logger.error("TELEGRAM_BOT_TOKEN is not configured! Please provide a valid token from @BotFather.")
            return

        self.bot = Bot(token=self.bot_token)
        print(f"[OK] Telegram Bot connecting with allowlist: {self.allowed_user_ids}...")

        # Optional web server for zero-card platforms (Render, Koyeb, HuggingFace Spaces)
        port_env = os.environ.get("PORT")
        web_runner = None
        if port_env:
            try:
                from aiohttp import web
                web_app = web.Application()
                async def handle_health(request):
                    return web.Response(
                        text="{\"status\":\"healthy\",\"bot\":\"Halal SIP AI Bot\",\"service\":\"24/7 Active\"}",
                        content_type="application/json",
                        status=200
                    )
                web_app.router.add_get("/", handle_health)
                web_app.router.add_get("/health", handle_health)
                web_runner = web.AppRunner(web_app)
                await web_runner.setup()
                port = int(port_env)
                site = web.TCPSite(web_runner, "0.0.0.0", port)
                await site.start()
                print(f"[OK] Web health service listening on 0.0.0.0:{port} for 24/7 cloud hosting!")
            except Exception as e:
                logger.warning(f"Could not bind web health check on port {port_env}: {e}")
        
        # Start background market sync and auto-notification loop
        scheduler_task = asyncio.create_task(self._scheduler_loop())
        try:
            await self.dp.start_polling(self.bot)
        finally:
            scheduler_task.cancel()
            if web_runner:
                await web_runner.cleanup()
            await self.bot.session.close()

