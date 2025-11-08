import os
import requests
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

class AdvancedCryptoBot:
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token)
        self.setup_handlers()
    
    def get_all_coins_list(self):
        """Get all available coins from CoinGecko"""
        try:
            url = "https://api.coingecko.com/api/v3/coins/list"
            response = requests.get(url)
            return {coin['symbol']: coin['id'] for coin in response.json()}
        except:
            return {}
    
    def find_coin_id(self, symbol):
        """Find coin ID from symbol"""
        coins_list = self.get_all_coins_list()
        return coins_list.get(symbol.lower())
    
    def get_coin_price(self, coin_input):
        """Get price for ANY coin"""
        try:
            # Remove special characters and convert to lowercase
            coin_input = re.sub(r'[^a-zA-Z0-9]', '', coin_input).lower()
            
            # First try direct ID match
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_input}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
            response = requests.get(url)
            data = response.json()
            
            if coin_input in data:
                return self.format_price_data(coin_input, data[coin_input])
            
            # If not found, search by symbol
            coin_id = self.find_coin_id(coin_input)
            if coin_id:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
                response = requests.get(url)
                data = response.json()
                
                if coin_id in data:
                    return self.format_price_data(coin_id, data[coin_id])
            
            return "❌ Coin not found. Please check the symbol and try again."
            
        except Exception as e:
            return "❌ Error fetching price data. Please try again later."
    
    def format_price_data(self, coin_id, data):
        """Format price data to look professional"""
        price = data.get('usd', 0)
        change_24h = data.get('usd_24h_change', 0)
        market_cap = data.get('usd_market_cap', 0)
        
        # Professional signal analysis
        if change_24h > 10:
            signal = "🚀 STRONG BUY"
            emoji = "📈"
            analysis = "Bullish momentum strong"
        elif change_24h > 3:
            signal = "🟢 BUY"
            emoji = "💹"
            analysis = "Positive trend"
        elif change_24h > -3:
            signal = "🟡 HOLD"
            emoji = "⚡"
            analysis = "Neutral market"
        elif change_24h > -10:
            signal = "🔴 SELL"
            emoji = "📉"
            analysis = "Downward pressure"
        else:
            signal = "💀 STRONG SELL"
            emoji = "🎯"
            analysis = "Heavy selling"
        
        # Format market cap
        if market_cap > 1e9:
            market_cap_str = f"${market_cap/1e9:.2B}"
        elif market_cap > 1e6:
            market_cap_str = f"${market_cap/1e6:.2f}M"
        else:
            market_cap_str = f"${market_cap:,.2f}"
        
        return f"""
{emoji} **{coin_id.upper()}** Analysis Report

💰 **Price:** ${price:,.4f}
📊 **24h Change:** {change_24h:+.2f}%
🏦 **Market Cap:** {market_cap_str}

🎯 **Trading Signal:** {signal}
📈 **Market Analysis:** {analysis}

💡 **Technical Outlook:**
{'✅ Bullish trend forming' if change_24h > 5 else '⚠️  Market consolidation' if change_24h > -5 else '❌ Bearish pressure'}

⚡ **Risk Level:** {'Low' if abs(change_24h) < 5 else 'Medium' if abs(change_24h) < 15 else 'High'}

📊 **Support/Resistance:**
Resistance: ${price * 1.05:,.2f}
Support: ${price * 0.95:,.2f}

#️⃣ **Hash Tags:** #{coin_id} #Crypto #Trading
"""
    
    def handle_message(self, update: Update, context: CallbackContext):
        """Handle ANY coin message"""
        user_message = update.message.text.strip()
        
        # Ignore commands
        if user_message.startswith('/'):
            return
        
        # Remove common words and get clean coin symbol
        clean_input = self.clean_coin_input(user_message)
        
        if clean_input:
            price_info = self.get_coin_price(clean_input)
            update.message.reply_text(price_info, parse_mode='Markdown')
        else:
            update.message.reply_text(
                "🤖 **Advanced Crypto Analysis Bot**\n\n"
                "Send me ANY coin name or symbol:\n"
                "• Bitcoin, BTC, btc\n"
                "• Ethereum, ETH, eth\n" 
                "• Solana, SOL, sol\n"
                "• Or ANY other coin!\n\n"
                "💡 **Examples:**\n"
                "`bitcoin` `ETH` `solana` `ADA` `DOT`\n"
                "`shib` `doge` `matic` `avax`\n\n"
                "🎯 I'll provide professional analysis!",
                parse_mode='Markdown'
            )
    
    def clean_coin_input(self, text):
        """Clean user input to extract coin symbol"""
        # Remove common words
        text = re.sub(r'\b(price|of|check|what.is|how.much|value)\b', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        # Extract potential coin symbol (2-10 characters, alphanumeric)
        match = re.search(r'[a-zA-Z0-9]{2,20}', text)
        if match:
            return match.group()
        return text if text and len(text) <= 20 else None
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        dp = self.updater.dispatcher
        
        # Handle all text messages
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        def start(update: Update, context: CallbackContext):
            update.message.reply_text(
                "🚀 **Welcome to Advanced Crypto Analysis Bot!**\n\n"
                "I can analyze ANY cryptocurrency:\n"
                "• Real-time prices\n• Professional signals\n• Market analysis\n• Risk assessment\n\n"
                "**Just send me any coin name or symbol!**\n\n"
                "💎 *Examples:* `BTC`, `ETH`, `SOL`, `ADA`, `DOT`, `MATIC`, `AVAX`, `SHIB`, *or any other coin!*",
                parse_mode='Markdown'
            )
        
        def price(update: Update, context: CallbackContext):
            if context.args:
                coin_input = ' '.join(context.args)
                price_info = self.get_coin_price(coin_input)
                update.message.reply_text(price_info, parse_mode='Markdown')
            else:
                update.message.reply_text(
                    "💡 **Usage:** `/price coin_name`\n\n"
                    "**Examples:**\n"
                    "• `/price bitcoin`\n• `/price ETH`\n• `/price solana`\n• `/price ADA`\n\n"
                    "I support **ALL** cryptocurrencies! 🚀",
                    parse_mode='Markdown'
                )
        
        def analyze(update: Update, context: CallbackContext):
            if context.args:
                coin_input = ' '.join(context.args)
                price_info = self.get_coin_price(coin_input)
                update.message.reply_text(price_info, parse_mode='Markdown')
            else:
                update.message.reply_text(
                    "🔍 **Advanced Analysis**\n\n"
                    "Usage: `/analyze coin_name`\n\n"
                    "Get professional trading analysis for any cryptocurrency!",
                    parse_mode='Markdown'
                )
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("price", price))
        dp.add_handler(CommandHandler("analyze", analyze))
        dp.add_handler(CommandHandler("analysis", analyze))
    
    def start_forever(self):
        """Start the 24/7 bot"""
        self.updater.start_polling()
        print("🤖 Advanced Crypto Bot is running 24/7...")
        self.updater.idle()

# Run the bot
if __name__ == '__main__':
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    if BOT_TOKEN:
        bot = AdvancedCryptoBot(BOT_TOKEN)
        bot.start_forever()
    else:
        print("❌ BOT_TOKEN not found in environment variables")
