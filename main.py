import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from discord_webhook import DiscordWebhook, DiscordEmbed
import time
import dotenv
import os
import nltk
from newspaper import Article
from datetime import datetime
import sys


dotenv.load_dotenv()    

WEBHOOK_URL = os.getenv('WEBHOOK_URL')

url = 'https://www.lemonde.fr'
previous_articles = set()

response = requests.get(url)

def get_article_urls():
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
    
        all_links = soup.find_all('a')

        article_urls = []

        for link in all_links:
            href = link.get('href')
            if href:
                    absolute_url = urljoin(url, href)
                    if 'lemonde.fr' in absolute_url and '/article/' in absolute_url:
                        article_urls.append(absolute_url)
                        
                    
        article_urls = set(article_urls)
        return article_urls





    

def send_rich_notification(article_url='https://www.lemonde.fr/international/article/2025/11/15/donald-trump-rompt-avec-marjorie-taylor-greene-figure-du-camp-maga-sur-l-affaire-epstein_6653493_3210.html', chatgpt_summary="Résumé généré par ChatGPT sera ajouté ici."):
    """
    Envoie une notification Discord enrichie pour un article du Monde.
    Le résumé est réservé pour l'insertion ultérieure par ChatGPT.
    """
    try:
        # Extraire les métadonnées de l'article
        article = Article(article_url, language='fr')
        article.download()
        article.parse()
        
        webhook = DiscordWebhook(
            url=WEBHOOK_URL,
            username="📰 Le Monde News"
        )
        
        # Titre (limitée à 256 caractères)
        title = article.title[:253] + "..." if len(article.title) > 256 else article.title
        
        # Embed principal
        embed = DiscordEmbed(
            title=title or "Nouvel article",
            description="Un nouvel article vient d'être publié sur Le Monde.",
            url=article_url,
            color='DC143C'
        )
        
        # Auteurs
        if article.authors:
            authors = ", ".join(article.authors[:3])
            embed.set_author(
                name=f"Par {authors}",
                url="https://www.lemonde.fr",
                icon_url="https://www.lemonde.fr/favicon.ico"
            )
        else:
            embed.set_author(
                name="Le Monde",
                url="https://www.lemonde.fr",
                icon_url="https://www.lemonde.fr/favicon.ico"
            )
        
        # Image principale
        if article.top_image:
            embed.set_image(url=article.top_image)
        
        # Miniature
        embed.set_thumbnail(
            url="https://www.lemonde.fr/dist/assets/img/logos/lm-miniature.png"
        )
        
        # Date de publication (si disponible)
        if article.publish_date:
            embed.add_embed_field(
                name="📅 Publié le",
                value=article.publish_date.strftime("%d/%m/%Y à %H:%M"),
                inline=True
            )
        
        # Nombre de mots
        word_count = len(article.text.split())
        embed.add_embed_field(
            name="📖 Longueur",
            value=f"{word_count} mots",
            inline=True
        )
        
        # Catégorie (extrait de l'URL)
        category = article_url.split('/')[3] if len(article_url.split('/')) > 3 else "Actualité"
        embed.add_embed_field(
            name="📂 Catégorie",
            value=category.capitalize(),
            inline=True
        )
        
        # Détection/heure actuelle
        embed.add_embed_field(
            name="⏰ Détecté à",
            value=datetime.now().strftime("%H:%M:%S"),
            inline=True
        )
        
        # Section réservée pour résumé ChatGPT
        embed.add_embed_field(
            name="🧠 Résumé ChatGPT",
            value=chatgpt_summary,
            inline=False
        )
        
        # Footer
        embed.set_footer(
            text="News Bot • Powered by Newspaper3k",
            icon_url="https://cdn.discordapp.com/embed/avatars/0.png"
        )
        
        # Timestamp
        embed.set_timestamp()
        
        # Envoi
        webhook.add_embed(embed)
        response = webhook.execute()
        
        if response.status_code in [200, 204]:
            print(f"✓ Notification envoyée: {title[:50]}...")
        else:
            print(f"✗ Erreur Discord: {response.status_code}")
    
    except Exception as e:
        print(f"✗ Erreur extraction : {e}")
        webhook = DiscordWebhook(
            url=WEBHOOK_URL,
            content=f"📰 **Nouvel article détecté**\n{article_url}"
        )
        webhook.execute()

# ===== BOUCLE PRINCIPALE DE SURVEILLANCE =====

print("=" * 50)
print("🚀 BOT DE SURVEILLANCE LE MONDE DÉMARRÉ")
print("=" * 50)

previous_articles = get_article_urls()
print(f"📊 {len(previous_articles)} articles initiaux chargés\n")
print("⏳ Surveillance en cours (vérification toutes les 60 secondes)...\n")


print(send_rich_notification())
sys.exit()


while True:
    time.sleep(60)  # Attendre 1 minute
    
    # Récupérer les articles actuels
    current_articles = get_article_urls()
    
    # Détecter les nouveaux articles
    new_articles = current_articles - previous_articles
    
    if new_articles:
        print(f"\n{'='*50}")
        print(f"🆕 {len(new_articles)} NOUVEAUX ARTICLES DÉTECTÉS!")
        print(f"{'='*50}\n")
        
        for article_url in new_articles:
            send_rich_notification(article_url)
            time.sleep(2)  # Pause de 2 secondes entre chaque notification (éviter rate limit Discord)
        
        print(f"\n✅ Toutes les notifications envoyées\n")
    else:
        print(f"⏳ Aucun nouveau contenu ({datetime.now().strftime('%H:%M:%S')})")
    
    # Mettre à jour la liste
    previous_articles = current_articles