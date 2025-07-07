# Pedro Promo Bot
Este é um bot de automação para o Telegram, desenvolvido em Python, que utiliza a sua própria conta de utilizador para monitorizar mensagens em tempo real. Ele filtra o conteúdo de todos os seus grupos com base numa lista de palavras-chave definidas por si e envia notificações privadas e formatadas, garantindo que você nunca mais perca uma promoção do seu interesse.

O que o Bot Realmente Faz: Não é um Bot Comum: Ao contrário da maioria dos bots, este não precisa de ser adicionado aos grupos de promoções. Ele funciona de uma forma mais inteligente e discreta.

Monitorização com a Sua Conta: O bot utiliza a biblioteca Telethon para se conectar ao Telegram como se fosse a sua própria conta de utilizador (usando as suas credenciais API_ID e API_HASH). Isto dá-lhe a capacidade de "ler" as mensagens de todos os grupos e canais em que a sua conta já participa.

Filtro Personalizado: Em paralelo, o bot utiliza a biblioteca python-telegram-bot para gerir os seus comandos. Através de uma conversa privada com o bot que você criou (o "bot de notificações"), pode:

Adicionar (/adicionar): Incluir novas palavras-chave (ex: "iphone 15 pro", "cadeira de escritório", "rtx 4080") na sua lista de desejos.

Listar (/listar): Ver todos os produtos que estão a ser monitorizados.

Deletar (/deletar): Remover itens que já não lhe interessam.

Notificação Instantânea: Assim que uma nova mensagem é publicada num dos grupos, o bot faz o seguinte:

1. Lê o texto da mensagem.
2. Compara o texto com cada uma das suas palavras-chave.
3. Se encontrar uma correspondência (ex: a palavra "monitor" na mensagem), ele imediatamente formata e envia uma notificação para si através do "bot de notificações".

Segurança e Privacidade: As suas credenciais sensíveis (API_ID, API_HASH, BOT_TOKEN) não ficam expostas no código. Elas são carregadas a partir de um ficheiro local .env, que é ignorado pelo Git através do .gitignore, garantindo que os seus dados nunca sejam partilhados acidentalmente.

Em resumo, o projeto é uma automação poderosa que combina a capacidade de leitura de uma conta de utilizador com a conveniência de um bot de notificações, criando um filtro de promoções altamente eficaz e personalizado.
