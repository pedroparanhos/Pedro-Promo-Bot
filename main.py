import logging
import asyncio
import os
import re
import sys

# Importa a função para carregar variáveis de ambiente do ficheiro .env
from dotenv import load_dotenv

# Importa os módulos do Telethon
from telethon import TelegramClient, events
# Importa o erro específico de senha 2FA diretamente para mais robustez
from telethon.errors import SessionPasswordNeededError

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Carrega as variáveis de ambiente do ficheiro .env
load_dotenv()

# --- CONFIGURAÇÕES SEGURAS (LIDAS DO AMBIENTE) ---
# As suas credenciais agora são lidas do ficheiro .env ou das variáveis de ambiente do sistema
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SEU_USER_ID = os.getenv("SEU_USER_ID")
KEYWORDS_FILE = 'keywords.txt'

# LISTA DE GRUPOS A IGNORAR (adicione mais nomes se necessário)
GROUP_BLACKLIST = ["Comentários"]

# Verifica se todas as credenciais foram carregadas
if not all([API_ID, API_HASH, BOT_TOKEN, SEU_USER_ID]):
    logging.critical("ERRO: Uma ou mais credenciais (API_ID, API_HASH, BOT_TOKEN, SEU_USER_ID) não foram encontradas. Verifique o seu ficheiro .env ou as variáveis de ambiente.")
    sys.exit(1) # Encerra o script se as credenciais estiverem em falta

# Converte o USER_ID para inteiro após a verificação
SEU_USER_ID = int(SEU_USER_ID)

# --- FIM DAS CONFIGURAÇÕES ---

# Configuração de logs para ajudar a identificar problemas
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Silencia logs muito verbosos de bibliotecas de terceiros
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- GERENCIAMENTO DA LISTA DE PRODUTOS (COM PERSISTÊNCIA) ---

def load_keywords():
    """Carrega as palavras-chave de um arquivo de texto."""
    if not os.path.exists(KEYWORDS_FILE):
        return []
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        logger.info(f"Palavras-chave carregadas: {keywords}")
        return keywords
    except Exception as e:
        logger.error(f"Erro ao carregar palavras-chave: {e}")
        return []

def save_keywords(keywords):
    """Salva a lista de palavras-chave em um arquivo de texto."""
    try:
        with open(KEYWORDS_FILE, 'w', encoding='utf-8') as f:
            for keyword in keywords:
                f.write(f"{keyword}\n")
        logger.info(f"Palavras-chave salvas: {keywords}")
    except Exception as e:
        logger.error(f"Erro ao salvar palavras-chave: {e}")

# Carrega as palavras-chave ao iniciar o bot
KEYWORDS = load_keywords()

# Estados para a conversa (adicionar/deletar produto)
STATE_ADD = 1
STATE_DELETE = 2

# --- Funções do Bot (Comandos) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia a conversa e mostra a mensagem de ajuda."""
    await update.message.reply_text(
        "Olá! Eu sou seu assistente de promoções. 🤖\n\n"
        "Eu leio as mensagens de todos os grupos em que você está e te notifico quando encontrar uma promoção com base nas suas palavras-chave.\n\n"
        "Use os seguintes comandos:\n"
        "▶️ /adicionar - Cadastra um novo produto na lista.\n"
        "📋 /listar - Exibe todos os produtos cadastrados.\n"
        "🗑️ /deletar - Remove um produto da sua lista.\n\n"
        "O filtro já está rodando em segundo plano!"
    )

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o processo de adicionar uma nova palavra-chave."""
    await update.message.reply_text(
        "Qual produto (palavra-chave) você quer adicionar à lista de monitoramento?\n\n"
        "Você pode cancelar a qualquer momento usando /cancelar."
    )
    return STATE_ADD

async def add_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Adiciona a palavra-chave recebida à lista."""
    product = update.message.text.strip().lower()
    if not product:
        await update.message.reply_text("O nome do produto não pode ser vazio. Tente novamente ou use /cancelar.")
        return STATE_ADD

    if product not in KEYWORDS:
        KEYWORDS.append(product)
        save_keywords(KEYWORDS)
        logger.info(f"Produto adicionado: {product}. Lista atual: {KEYWORDS}")
        await update.message.reply_text(
            f"✅ Pronto! O produto '{product}' foi adicionado à sua lista."
        )
    else:
        await update.message.reply_text(
            f"⚠️ O produto '{product}' já está na sua lista."
        )
    return ConversationHandler.END

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe a lista de palavras-chave cadastradas."""
    if not KEYWORDS:
        await update.message.reply_text("Sua lista de monitoramento está vazia. Use /adicionar para incluir um produto.")
    else:
        message = "Estes são os produtos que estou monitorando:\n\n"
        for keyword in sorted(KEYWORDS):
            message += f"• `{keyword}`\n"
        await update.message.reply_text(message, parse_mode='Markdown')

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o processo de deletar uma palavra-chave."""
    if not KEYWORDS:
        await update.message.reply_text("Sua lista já está vazia. Não há nada para remover.")
        return ConversationHandler.END

    reply_keyboard = [[keyword] for keyword in sorted(KEYWORDS)]
    await update.message.reply_text(
        "Qual produto você quer remover da lista? (Clique em um botão ou digite o nome)\n\n"
        "Use /cancelar se mudar de ideia.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Escolha um produto para remover..."
        ),
    )
    return STATE_DELETE

async def delete_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Remove a palavra-chave da lista."""
    product_to_delete = update.message.text.strip().lower()
    if product_to_delete in KEYWORDS:
        KEYWORDS.remove(product_to_delete)
        save_keywords(KEYWORDS)
        logger.info(f"Produto removido: {product_to_delete}. Lista atual: {KEYWORDS}")
        await update.message.reply_text(
            f"🗑️ O produto '{product_to_delete}' foi removido com sucesso.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            f"🤔 Não encontrei o produto '{product_to_delete}' na sua lista. Tente novamente.",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação atual e encerra a conversa."""
    await update.message.reply_text(
        "Operação cancelada.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# --- Lógica do Telethon (Leitor de Mensagens) ---

telethon_client = TelegramClient('promo_session', int(API_ID), API_HASH)

async def telethon_event_handler(event, bot_app: Application, bot_id: int):
    """Processa cada nova mensagem recebida nos seus grupos."""
    # CORREÇÃO ANTI-LOOP: Ignora mensagens enviadas por você mesmo ou pelo próprio bot de notificações.
    if event.message.out or event.sender_id == bot_id:
        return

    chat_title = getattr(event.chat, 'title', 'Chat Privado')
    
    # VERIFICA SE O GRUPO ESTÁ NA LISTA NEGRA
    if chat_title in GROUP_BLACKLIST:
        logger.info(f"Ignorando mensagem do grupo '{chat_title}' pois está na lista negra.")
        return

    if not event.raw_text:
        return

    logger.info(f"--- Nova Mensagem no grupo '{chat_title}' ---")
    
    message_text = event.raw_text.lower()
    logger.info(f"Texto: \"{message_text[:200]}...\"")

    for keyword_phrase in KEYWORDS[:]:
        logger.info(f"-> Verificando a palavra-chave: '{keyword_phrase}'")

        required_words = keyword_phrase.split()
        
        try:
            all_words_found = all(re.search(r'\b' + re.escape(word) + r'\b', message_text) for word in required_words)
            logger.info(f"   Resultado da verificação para '{keyword_phrase}': {all_words_found}")
        except re.error as e:
            logger.warning(f"   Erro de Regex com a palavra-chave '{keyword_phrase}': {e}")
            all_words_found = False

        if all_words_found:
            logger.info(f"!!! SUCESSO! Frase-chave encontrada: '{keyword_phrase}' no grupo '{chat_title}' !!!")
            
            link_da_mensagem = f"https://t.me/c/{event.chat_id}/{event.message.id}"
            
            mensagem_formatada = (
                f"🔥 **Promoção Encontrada!** 🔥\n\n"
                f"**Produto:** `{keyword_phrase}`\n"
                f"**Grupo:** `{chat_title}`\n\n"
                f"**Texto Original:**\n_{event.raw_text}_\n\n"
                f"➡️ [Ver Mensagem]({link_da_mensagem})"
            )
            
            try:
                await bot_app.bot.send_message(
                    chat_id=SEU_USER_ID, text=mensagem_formatada, parse_mode='Markdown'
                )
                logger.info("   Notificação enviada com sucesso.")
            except Exception as e:
                logger.error(f"   Falha ao enviar notificação: {e}")

            break

# --- Função Principal (Lógica de Inicialização Corrigida) ---

async def main() -> None:
    """Inicia o bot e o leitor de mensagens de forma assíncrona."""
    
    application = Application.builder().token(BOT_TOKEN).build()

    # Obtém o ID do próprio bot para o ignorar mais tarde e evitar loops
    bot_user = await application.bot.get_me()
    BOT_ID = bot_user.id
    logger.info(f"ID do Bot é {BOT_ID}. Mensagens deste ID serão ignoradas.")

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("adicionar", add_command),
            CommandHandler("deletar", delete_command),
        ],
        states={
            STATE_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_received)],
            STATE_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_received)],
        },
        fallbacks=[CommandHandler("cancelar", cancel_command)],
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("listar", list_command))
    application.add_handler(conv_handler)

    # Conecta o cliente Telethon
    await telethon_client.connect()
    if not await telethon_client.is_user_authorized():
        logger.error("Cliente Telethon não autorizado. Por favor, execute interativamente para fazer o login.")
        phone_number = input('Por favor, insira seu número de telefone (formato +55119...): ')
        await telethon_client.send_code_request(phone_number)
        try:
            await telethon_client.sign_in(phone_number, input('Insira o código que você recebeu: '))
        except SessionPasswordNeededError:
            await telethon_client.sign_in(password=input('Sua conta tem verificação em duas etapas. Insira sua senha: '))
        
    # Adiciona o handler de eventos, passando o ID do bot para ser ignorado
    telethon_client.add_event_handler(
        lambda event: telethon_event_handler(event, application, BOT_ID),
        events.NewMessage
    )
    logger.info("Cliente Telethon iniciado e escutando por mensagens...")

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        logger.info("Bot de comandos iniciado...")
        
        await telethon_client.run_until_disconnected()
        
        await application.updater.stop()
        await application.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot encerrado.")
    except Exception as e:
        logger.critical(f"Ocorreu um erro crítico: {e}")