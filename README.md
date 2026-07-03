# Plateforme Intelligente de Gestion des Partenariats Huawei

<p align="center">
  <b>Recherche Vectorielle Sémantique • Diagnostics IA en Streaming • Génération de Propositions B2B</b>
</p>

<p align="center">
  <i>Moteur de matching propulsé par l'IA, développé avec FastAPI et Ollama,
intégrant la recherche vectorielle pgvector (Supabase) pour aligner les besoins
clients avec les partenaires Huawei les plus pertinents en Tunisie.</i>
</p>

<br>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" />
</div>

<br>

<div align="center">
  <img src="https://img.shields.io/badge/Search-Vector%20Semantic-informational?style=flat-square" />
  <img src="https://img.shields.io/badge/Embeddings-nomic--embed--text%20(768d)-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Streaming-Server--Sent%20Events-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Database-pgvector-blue?style=flat-square" />
</div>

<br><br>

<p align="center">
  <a href="#archi">Architecture</a> •
  <a href="#install">Installation</a> •
  <a href="#api">API Endpoints</a> •
  <a href="#workflow">Guide d'Utilisation</a> •
  <a href="#secu">Sécurité</a> •
  <a href="#conclusion">Conclusion</a> •
  <a href="#contacts">Contacts</a>
</p>

<br>

#### Bienvenue sur la plateforme de gestion intelligente des partenariats Huawei.

Cette application aide les équipes commerciales de **Huawei** à identifier, en temps réel,
le **meilleur partenaire intégrateur** capable de répondre à un besoin client donné. Au lieu
d'une simple recherche par mots-clés, le système utilise la **recherche vectorielle sémantique** :
il comprend le *sens* d'une demande (ex. « infrastructure de stockage cloud et communication de
données ») et la compare mathématiquement aux capacités réelles de chaque partenaire.

Pour chaque partenaire identifié, l'application :
1. **Calcule un score de similarité** entre le besoin et le profil du partenaire ;
2. **Affiche des indicateurs stratégiques** : santé du partenariat, niveau de risque, tendance d'engagement, valeur future estimée ;
3. **Génère un diagnostic d'alignement** rédigé par une IA, en streaming, mot par mot ;
4. **Produit automatiquement une proposition commerciale B2B** formelle prête à l'envoi.

Un bouton **Meeting Assistant** dans la barre de navigation permet également d'ouvrir
l'application compagnon *AI Meeting Assistant* (projet séparé, servi sur le port `8001`).

---

<div id="archi"></div>

> ### Architecture et Modélisation technique

Le projet repose sur une infrastructure conçue pour combiner recherche sémantique et génération
de texte par IA, entièrement exécutée en local via Ollama.

```
┌──────────────┐    requête client       ┌─────────────────────┐
│  index.html  │ ──────────────────────► │   FastAPI (app.py)  │
│  (interface) │ ◄───── streaming ────── │                     │
└──────────────┘   (SSE temps réel)      └──────────┬──────────┘
                                                    │
                       ┌────────────────────────────┼───────────────────────┐
                       ▼                            ▼                       ▼
              ┌─────────────────┐         ┌────────────────────┐   ┌──────────────────┐
              │     Ollama      │         │      Supabase      │   │     Ollama       │
              │ nomic-embed-text│         │  (PostgreSQL +     │   │     llama3       │
              │  → vecteur 768  │         │   pgvector)        │   │ → texte généré   │
              └─────────────────┘         │  fonction RPC      │   └──────────────────┘
                 (embeddings)             │  match_partners    │     (diagnostics +
                                          └────────────────────┘      propositions)
```

**Étapes d'une recherche**
* **Vectorisation** : le backend transforme le besoin client en **vecteur de 768 dimensions** via le modèle local `nomic-embed-text` (Ollama).
* **Recherche par similarité** : ce vecteur est envoyé à Supabase, qui exécute la fonction SQL **`match_partners`** calculant la **similarité cosinus** entre la requête et les embeddings des partenaires stockés.
* **Diagnostic IA** : le modèle `llama3` génère un **diagnostic stratégique** pour chaque partenaire correspondant, diffusé en **streaming (SSE)** mot par mot.
* **Proposition commerciale** : sur demande, une **proposition de partenariat B2B** complète est générée automatiquement.

**Conception de la Base de Données**
Le système s'appuie sur une base de données relationnelle **PostgreSQL** (Supabase) enrichie de
l'extension **`pgvector`**. La table `partner_profiles` combine les données métier des partenaires
et leur représentation sémantique (`vector(768)`), permettant une recherche par proximité vectorielle.

| Colonne                  | Type          | Description                              |
|--------------------------|---------------|------------------------------------------|
| `id`                     | `bigint`      | Identifiant unique                       |
| `company_name`           | `text`        | Nom du partenaire                        |
| `industry`               | `text`        | Secteur d'activité                       |
| `objectives`             | `text`        | Capacités et spécialisations             |
| `embedding`              | `vector(768)` | Vecteur sémantique généré par l'IA       |
| `health_score`           | `integer`     | Score de santé du partenariat (0–100)    |
| `risk_level`             | `text`        | Niveau de risque (Low / Medium / High)   |
| `engagement_trend`       | `text`        | Tendance d'engagement                    |
| `future_value_estimate`  | `text`        | Valeur future estimée                    |

**Stack technique**
| Couche              | Technologie                                             |
|---------------------|--------------------------------------------------------|
| **Backend**         | Python · FastAPI · Uvicorn                             |
| **Base de données** | Supabase (PostgreSQL 17 + extension `pgvector`)       |
| **IA / Embeddings** | Ollama — `nomic-embed-text` (vecteurs 768 dimensions) |
| **IA générative**   | Ollama — `llama3`                                     |
| **Streaming**       | Server-Sent Events (`sse-starlette`)                  |
| **Frontend**        | HTML / CSS / JavaScript (page unique `index.html`)    |
| **Config**          | `python-dotenv` (fichier `.env`)                      |

<div id="install"></div>

> ### Installation et Configuration

Pour déployer ce projet localement, suivez les étapes ci-dessous :

**Prérequis** : **Python 3.10+**, un projet **Supabase** (table `partner_profiles` + fonction `match_partners`),
et **Ollama** installé avec les deux modèles :
```bash
ollama pull nomic-embed-text
ollama pull llama3
```

1. **Clonage du projet**
   ```bash
   git clone https://github.com/YuuMii05/Development-of-an-Intelligent-Corporate-Partnership-Management-Platform.git
   cd partner-backend
   ```

2. **Variables d'environnement**
   Créez un fichier `.env` à la racine (le domaine se termine bien par **`.co`**, et non `.com`) :
   ```bash
   SUPABASE_URL="https://<votre-projet>.supabase.co"
   SUPABASE_SERVICE_KEY="<votre-clé-supabase>"
   ```

3. **Installation des dépendances**
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   pip install -r requirements.txt
   ```

4. **Initialisation de la base (une seule fois)**
   ```bash
   python seed_partners.py   # 7 partenaires de base
   python add_partners.py    # + 12 partenaires Huawei Tunisie (19 au total)
   ```
   `seed_partners.py` vide la table, génère un embedding pour chaque partenaire via Ollama, puis
   insère les profils dans Supabase. `add_partners.py` complète la base en ignorant automatiquement
   les doublons déjà présents.

5. **Lancement de l'application**
   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000 --reload
   ```
   Puis ouvrir **http://127.0.0.1:8000**

<div id="api"></div>

> ### Points de terminaison (Endpoints) de l'API

Cette section répertorie les routes disponibles pour interagir avec le moteur de matching.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/` | Sert l'interface utilisateur (`index.html`) |
| `GET` | `/stream-match` | Recherche sémantique + diagnostic IA en streaming (SSE) |
| `POST` | `/generate-proposal` | Génère une proposition de partenariat B2B formelle |

**Exemple — `/stream-match`**
```
GET /stream-match?query=infrastructure de stockage cloud
```
Événements SSE renvoyés :
* `initial_matches` — la liste des partenaires correspondants ;
* `ai_chunk` — fragments du diagnostic IA, en temps réel ;
* `done` — fin du flux.

---

<div id="workflow"></div>

> ### Guide d'Utilisation (Workflow)

Pour tester l'intégralité du flux de travail, suivez ces étapes :
1. **Saisir un besoin** : entrez une demande client dans l'interface (ex. « solution de stockage et sauvegarde des données »).
2. **Lancer la recherche** : le système renvoie instantanément les partenaires les plus proches, avec leurs indicateurs stratégiques.
3. **Lire le diagnostic IA** : un diagnostic d'alignement s'écrit en temps réel (streaming) sous chaque partenaire.
4. **Générer une proposition** : cliquez sur le bouton d'un partenaire pour produire automatiquement une proposition commerciale B2B prête à l'envoi.

### Structure du Projet
```text
partner-backend/
├── app.py              # Application FastAPI (point d'entrée principal)
├── seed_partners.py    # Initialisation : insère les 7 partenaires de base + embeddings
├── add_partners.py     # Ajoute 12 partenaires Huawei Tunisie supplémentaires (sans doublons)
├── index.html          # Interface utilisateur complète
├── .env                # Variables secrètes (non inclut sur Git)
├── logo.jpg / lp1.jpg  # Ressources visuelles
└── requirements.txt    # Dépendances Python
```

<div id="secu"></div>

> ### Sécurité

La protection des accès et des données repose sur les principes suivants :
* **Secrets isolés** : les clés et URL sont chargées depuis `.env`, jamais codées en dur dans le code.
* **Fichier ignoré** : le fichier `.env` est exclu du versioning via `.gitignore`.
* **Recommandation production** : activer le *Row Level Security (RLS)* sur la table `partner_profiles` avec des politiques de lecture, puis utiliser une clé *secret* dédiée côté serveur.

<div id="conclusion"></div>

> ### Conclusion

Ce projet met en pratique l'intégralité d'un pipeline d'IA appliquée au métier : de la **vectorisation
sémantique** des besoins clients à la **recherche par similarité** dans PostgreSQL/pgvector, jusqu'à la
**génération de diagnostics et de propositions** en streaming via Ollama. Le résultat est une solution
fonctionnelle et opérationnelle, validée sur **19 partenaires de référence**, prête pour une intégration
commerciale.

<div id="contacts"></div>

> ### Contact

* **Maram Bougossa** - [GitHub](https://github.com/YuuMii05)

---

<p align="right"><a href="#top">Retour au menu</a></p>
