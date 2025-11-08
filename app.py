import os
import requests
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global coin list cache
coin_list_cache = None

def get_all_coins_list():
    """Get all coins list from CoinGecko"""
    global coin_list_cache
    try:
        if coin_list_cache is None:
            url = "https://api.coingecko.com/api/v3/coins/list"
            response = requests.get(url, timeout=10)
            coins = response.json()
            # Create mapping for both symbol and name
            coin_list_cache = {}
            for coin in coins:
                coin_list_cache[coin['symbol'].upper()] = coin['id']
                coin_list_cache[coin['name'].upper()] = coin['id']
            logger.info(f"Loaded {len(coin_list_cache)} coins")
        return coin_list_cache
    except Exception as e:
        logger.error(f"Error loading coin list: {e}")
        return {}

def find_coin_id(user_input):
    """Find coin ID from user input"""
    coins = get_all_coins_list()
    user_input = user_input.upper().strip()
    
    # Direct match
    if user_input in coins:
        return coins[user_input]
    
    # Remove spaces and special characters
    clean_input = re.sub(r'[^A-Z0-9]', '', user_input)
    if clean_input in coins:
        return coins[clean_input]
    
    return None

def get_coin_price(coin_id):
    """Get price data for any coin"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if coin_id in data:
            return data[coin_id]
        return None
    except Exception as e:
        logger.error(f"Error fetching price for {coin_id}: {e}")
        return None

def generate_signal(change_24h, market_cap):
    """Generate professional trading signal"""
    if change_24h > 15:
        signal = "🚀 STRONG BUY"
        reason = "Very bullish momentum"
    elif change_24h > 7:
        signal = "🟢 BUY"
        reason = "Bullish trend"
    elif change_24h > 2:
        signal = "🟡 HOLD"
        reason = "Moderate growth"
    elif change_24h > -5:
        signal = "🟡 HOLD"
        reason = "Market consolidation"
    elif change_24h > -12:
        signal = "🔴 SELL"
        reason = "Downward pressure"
    else:
        signal = "💀 STRONG SELL"
        reason = "Heavy selling"
    
    # Adjust based on market cap
    if market_cap and market_cap < 100000000:  # < $100M
        signal += " ⚠️"
        reason += " (Low cap - High risk)"
    
    return signal, reason

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🚀 **Advanced Crypto Bot Started!**\n\n"
        "I support **ALL cryptocurrencies** from Binance and other exchanges!\n\n"
        "**Examples:**\n"
        "• Bitcoin, BTC, btc\n"
        "• Ethereum, ETH, eth\n" 
        "• Solana, SOL, sol\n"
        "• Shiba Inu, SHIB, shib\n"
        "• Or ANY other coin!\n\n"
        "Just send me any coin name or symbol! 🎯",
        parse_mode='Markdown'
    )

def handle_message(update: Update, context: CallbackContext):
    try:
        user_message = update.message.text.strip()
        logger.info(f"User asked for: {user_message}")
        
        if not user_message:
            update.message.reply_text("Please send me a coin name or symbol!")
            return
        
        # Find coin ID
        coin_id = find_coin_id(user_message)
        
        if not coin_id:
            update.message.reply_text(
                "❌ Coin not found!\n\n"
                "**Try these popular coins:**\n"
                "BTC, ETH, SOL, ADA, XRP, DOT, DOGE, BNB, MATIC, LTC, AVAX, LINK, SHIB\n\n"
                "Or make sure the spelling is correct!",
                parse_mode='Markdown'
            )
            return
        
        # Get price data
        price_data = get_coin_price(coin_id)
        
        if not price_data:
            update.message.reply_text("❌ Could not fetch price data. Please try again.")
            return
        
        price = price_data.get('usd', 0)
        change_24h = price_data.get('usd_24h_change', 0) or 0
        market_cap = price_data.get('usd_market_cap', 0)
        
        # Generate professional analysis
        signal, reason = generate_signal(change_24h, market_cap)
        
        # Format market cap
        if market_cap > 1e9:
            market_cap_str = f"${market_cap/1e9:.2f}B"
        elif market_cap > 1e6:
            market_cap_str = f"${market_cap/1e6:.2f}M"
        else:
            market_cap_str = f"${market_cap:,.0f}"
        
        # Create professional message
        message = f"""
🎯 **{coin_id.upper()} Analysis**

💰 **Price:** ${price:,.4f}
📈 **24h Change:** {change_24h:+.2f}%
🏦 **Market Cap:** {market_cap_str}

🔮 **Trading Signal:** {signal}
📊 **Analysis:** {reason}

⚡ **Risk Level:** {'Low' if abs(change_24h) < 5 else 'Medium' if abs(change_24h) < 15 else 'High'}
📉 **Support/Resistance:**
Resistance: ${price * 1.05:,.2f}
Support: ${price * 0.95:,.2f}

#️⃣ **Tags:** #{coin_id.replace('-', '')} #Crypto #Trading
        """
        
        update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text(
            "❌ Error processing request. Please try again with a different coin."
        )

def search_coin(update: Update, context: CallbackContext):
    """Search for coins"""
    if not context.args:
        update.message.reply_text("Usage: /search coin_name")
        return
    
    search_term = ' '.join(context.args)
    coins = get_all_coins_list()
    
    # Find matching coins
    matches = []
    for key, coin_id in coins.items():
        if search_term.upper() in key.upper():
            matches.append((key, coin_id))
            if len(matches) >= 10:  # Limit results
                break
    
    if matches:
        result = "🔍 **Search Results:**\n\n"
        for key, coin_id in matches[:8]:  # Show first 8 results
            result += f"• {key} → {coin_id}\n"
        update.message.reply_text(result, parse_mode='Markdown')
    else:
        update.message.reply_text("❌ No coins found matching your search.")

def main():
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found")
        return
    
    logger.info("🤖 Starting Advanced Crypto Bot...")
    
    # Pre-load coin list
    get_all_coins_list()
    
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("search", search_coin))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    logger.info("🤖 Advanced Crypto Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
