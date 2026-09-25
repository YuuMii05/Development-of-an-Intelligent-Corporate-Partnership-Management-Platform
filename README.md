# Plateforme Intelligente de Gestion des Partenariats Huawei

<p align="center">
  <b>Classement Sémantique des Partenaires • Diagnostics IA en Streaming • Propositions B2B • Assistant de Réunion</b>
</p>

<p align="center">
  <i>Plateforme propulsée par l'IA, développée avec FastAPI et Ollama, intégrant la recherche
vectorielle pgvector (Supabase) pour aider les équipes Huawei à trouver le partenaire idéal
pour chaque idée de projet en Tunisie, et à organiser leurs réunions.</i>
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
  <img src="https://img.shields.io/badge/LLM-llama3-red?style=flat-square" />
  <img src="https://img.shields.io/badge/Streaming-Server--Sent%20Events-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Database-pgvector-blue?style=flat-square" />
</div>

<br><br>

<p align="center">
  <a href="#archi">Architecture</a> •
  <a href="#meeting">Meeting Assistant</a> •
  <a href="#install">Installation</a> •
  <a href="#api">API Endpoints</a> •
  <a href="#workflow">Guide d'Utilisation</a> •
  <a href="#secu">Sécurité</a> •
  <a href="#conclusion">Conclusion</a> •
  <a href="#contacts">Contacts</a>
</p>

<br>

#### Bienvenue sur la plateforme de gestion intelligente des partenariats Huawei.

Cette application est destinée aux **employés Huawei chargés de contacter les partenaires et
de proposer des idées de partenariat**. Au lieu de parcourir un par un tous les partenaires,
l'employé décrit simplement son **idée de projet** : la plateforme **classe automatiquement tous
les partenaires** avec un **pourcentage de correspondance**, et met en avant les plus pertinents.

Le système utilise la **recherche vectorielle sémantique** : il comprend le *sens* d'une demande
(ex. « data lake IA avec stockage haute performance pour une banque ») et la compare
mathématiquement aux capacités réelles de chaque partenaire.

Pour chaque recherche, l'application :
1. **Classe les 19 partenaires** par pourcentage de correspondance (similarité cosinus), du meilleur au moins pertinent ;
2. **Affiche le profil réel de chaque partenaire** : niveau de partenariat Huawei, secteur, adresse, contact et capacités certifiées ;
3. **Génère un diagnostic d'alignement IA** pour les 3 meilleurs partenaires, en streaming, basé uniquement sur leur profil réel (aucun chiffre inventé) ;
4. **Produit une proposition commerciale B2B** formelle pour n'importe quel partenaire, en un clic.

La plateforme inclut aussi un **AI Meeting Assistant** (dossier [`meeting-assistant/`](meeting-assistant/)),
accessible via le bouton **Meeting Assistant** de la barre de navigation : il transforme les notes de
réunion en rapport structuré avec des **indicateurs chiffrés**, et propose un **chatbot** pour aider
l'employé à planifier et organiser son travail.

---

<div id="archi"></div>

> ### Architecture et Modélisation technique

Le projet repose sur une infrastructure conçue pour combiner recherche sémantique et génération
de texte par IA, entièrement exécutée en local via Ollama.

```
┌──────────────┐    idée de projet       ┌─────────────────────┐
│  index.html  │ ──────────────────────► │   FastAPI (app.py)  │
│  (interface) │ ◄───── streaming ────── │     port 8000       │
└──────────────┘     (SSE temps réel)    └──────────┬──────────┘
                                                    │
                       ┌────────────────────────────┼───────────────────────┐
                       ▼                            ▼                       ▼
              ┌─────────────────┐         ┌────────────────────┐   ┌──────────────────┐
              │     Ollama      │         │      Supabase      │   │     Ollama       │
              │ nomic-embed-text│         │  (PostgreSQL +     │   │     llama3       │
              │  → vecteur 768  │         │   pgvector)        │   │ → texte généré   │
              └─────────────────┘         │  fonction RPC      │   └──────────────────┘
                 (embeddings)             │  match_partners    │      (diagnostics +
                                          └────────────────────┘       propositions)
```

**Étapes d'une recherche**
* **Vectorisation** : le backend transforme l'idée de projet en **vecteur de 768 dimensions** via le modèle local `nomic-embed-text` (Ollama).
* **Classement par similarité** : ce vecteur est envoyé à Supabase, qui exécute la fonction SQL **`match_partners`** calculant la **similarité cosinus** entre la requête et chaque partenaire. Tous les partenaires sont renvoyés, triés du plus pertinent au moins pertinent.
* **Diagnostic IA** : le modèle `llama3` rédige un **diagnostic d'alignement** pour les 3 meilleurs partenaires, diffusé en **streaming (SSE)** mot par mot. Il n'utilise que les données réelles du partenaire (secteur, capacités, pourcentage de correspondance) et a pour consigne de ne jamais inventer de chiffres.
* **Proposition commerciale** : sur demande, une **proposition de partenariat B2B** complète est générée, sans montants, dates ni statistiques inventés.

**Mode hors ligne**
Si Supabase ou le backend est indisponible, l'interface bascule automatiquement sur l'annuaire
local des 19 partenaires avec une **recherche par mots-clés** (badge « Keyword match »), afin que
l'employé puisse toujours consulter les partenaires.

**Conception de la Base de Données**
Le système s'appuie sur une base de données relationnelle **PostgreSQL** (Supabase) enrichie de
l'extension **`pgvector`**. La table `partner_profiles` combine les données métier des partenaires
et leur représentation sémantique (`vector(768)`). Le script [`supabase_setup.sql`](supabase_setup.sql)
crée l'extension, la table et la fonction `match_partners`.

| Colonne                  | Type          | Description                              |
|--------------------------|---------------|------------------------------------------|
| `id`                     | `bigint`      | Identifiant unique                       |
| `company_name`           | `text`        | Nom du partenaire (unique)               |
| `industry`               | `text`        | Secteur d'activité                       |
| `objectives`             | `text`        | Capacités et spécialisations             |
| `embedding`              | `vector(768)` | Vecteur sémantique généré par l'IA       |

**Stack technique**
| Couche              | Technologie                                             |
|---------------------|--------------------------------------------------------|
| **Backend**         | Python · FastAPI · Uvicorn                             |
| **Base de données** | Supabase (PostgreSQL 17 + extension `pgvector`)       |
| **IA / Embeddings** | Ollama — `nomic-embed-text` (vecteurs 768 dimensions) |
| **IA générative**   | Ollama — `llama3`                                     |
| **Streaming**       | Server-Sent Events (`sse-starlette`)                  |
| **Frontend**        | HTML / CSS / JavaScript (pages uniques `index.html`)  |
| **Config**          | `python-dotenv` (fichier `.env`)                      |

---

<div id="meeting"></div>

> ### AI Meeting Assistant

Application compagnon (dossier `meeting-assistant/`, API sur le port `8001`) qui aide l'employé à
obtenir des **notes de réunion claires et exploitables**.

**Analyse d'un compte rendu** : l'employé colle ses notes ou la transcription de la réunion
(idéalement au format `Nom : texte`). L'IA (`llama3`) **extrait uniquement les faits présents dans
le texte** (participants, décisions, tâches, responsables, échéances, risques, questions ouvertes),
puis le serveur **calcule les indicateurs en Python** :

| Indicateur | Calcul |
|------------|--------|
| **Action Items** | Nombre de tâches, réparties par priorité (haute / moyenne / basse) |
| **Owner Assigned** | % des tâches ayant un responsable nommé |
| **Deadline Set** | % des tâches ayant une échéance |
| **Accountability Rate** | % des tâches ayant à la fois un responsable et une échéance |
| **Decisions / Open Questions** | Nombre de décisions prises et de points non résolus |
| **Resolution Rate** | Décisions ÷ (décisions + questions ouvertes) |
| **Risks / Blockers** | Nombre de risques ou blocages mentionnés |
| **Participation Share** | % de mots prononcés par chaque participant (ou nombre de mentions) |

Un responsable ou une échéance proposé(e) par l'IA mais **absent(e) du texte est rejeté(e)**
(« Not specified »), afin que les pourcentages reflètent fidèlement la réunion. Le résultat
comprend un tableau de bord, un tableau des tâches et un **rapport éditable** prêt à copier
(résumé, décisions, tâches, risques, questions ouvertes, e-mail de suivi).

**Chatbot** : une bulle de discussion permet de poser des questions à `llama3` pour planifier et
organiser le travail (réponses courtes, dans la langue de l'utilisateur).

---

<div id="install"></div>

> ### Installation et Configuration

Pour déployer ce projet localement, suivez les étapes ci-dessous :

**Prérequis** : **Python 3.10+**, un projet **Supabase**, **VS Code** avec l'extension
**Live Server** (optionnel), et **Ollama** installé avec les deux modèles :
```bash
ollama pull nomic-embed-text
ollama pull llama3
```

1. **Clonage du projet**
   ```bash
   git clone https://github.com/YuuMii05/Development-of-an-Intelligent-Corporate-Partnership-Management-Platform.git
   cd Development-of-an-Intelligent-Corporate-Partnership-Management-Platform
   ```

2. **Variables d'environnement**
   Créez un fichier `.env` à la racine (le domaine se termine bien par **`.co`**, et non `.com`) :
   ```bash
   SUPABASE_URL="https://<votre-projet>.supabase.co"
   SUPABASE_SERVICE_KEY="<votre-clé-secrète-supabase>"
   ```

3. **Installation des dépendances**
   ```bash
   python -m venv venv
   venv\Scripts\activate          # Windows
   pip install -r requirements.txt
   pip install -r meeting-assistant/requirements.txt
   ```

4. **Initialisation de la base (une seule fois)**
   Dans le tableau de bord Supabase, ouvrez **SQL Editor**, collez le contenu de
   [`supabase_setup.sql`](supabase_setup.sql) et exécutez-le (extension `pgvector`, table
   `partner_profiles` et fonction `match_partners`). Puis remplissez la table :
   ```bash
   python seed_partners.py   # 7 partenaires de base
   python add_partners.py    # + 12 partenaires Huawei Tunisie (19 au total)
   ```
   Les deux scripts génèrent un embedding pour chaque partenaire via Ollama, puis insèrent les
   profils dans Supabase. Ils ignorent automatiquement les partenaires déjà présents (aucune
   suppression de données).

5. **Lancement des deux API** (deux terminaux)
   ```bash
   # Terminal 1 — plateforme de partenariats (port 8000)
   uvicorn app:app --host 127.0.0.1 --port 8000

   # Terminal 2 — Meeting Assistant (port 8001)
   cd meeting-assistant
   uvicorn app:app --host 127.0.0.1 --port 8001
   ```

6. **Ouverture des interfaces**
   * **Plateforme** : http://127.0.0.1:8000, ou `index.html` via **Live Server** (port `5500`).
   * **Meeting Assistant** : http://127.0.0.1:8001, ou `meeting-assistant/index.html` via
     **Live Server** en ouvrant le dossier `meeting-assistant` dans VS Code (port `5501`, déjà
     configuré dans `meeting-assistant/.vscode/settings.json`).

   Les pages ouvertes via Live Server appellent automatiquement les API sur les ports `8000` et
   `8001` : ces deux serveurs doivent donc être lancés.

> **Note Supabase (offre gratuite)** : un projet inactif pendant environ une semaine est mis en
> pause. Il suffit de se connecter au tableau de bord Supabase pour le réactiver (quelques minutes).
> Pendant la pause, la plateforme fonctionne en mode hors ligne (recherche par mots-clés).

<div id="api"></div>

> ### Points de terminaison (Endpoints) de l'API

**Plateforme de partenariats — `app.py` (port 8000)**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/` | Sert l'interface utilisateur (`index.html`) |
| `GET` | `/stream-match` | Classement sémantique de tous les partenaires + diagnostic IA (top 3) en streaming (SSE) |
| `POST` | `/generate-proposal` | Génère une proposition de partenariat B2B formelle |

**Exemple — `/stream-match`**
```
GET /stream-match?query=data lake IA avec stockage haute performance pour une banque
```
Événements SSE renvoyés :
* `initial_matches` — tous les partenaires classés (`company_name`, `industry`, `objectives`, `similarity`) ;
* `ai_chunk` — fragments du diagnostic IA des 3 meilleurs partenaires, en temps réel ;
* `done` — fin du flux ;
* `error` — erreur (l'interface bascule alors en mode hors ligne).

**Meeting Assistant — `meeting-assistant/app.py` (port 8001)**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/` | Sert l'interface du Meeting Assistant |
| `POST` | `/analyze-meeting` | Analyse une transcription : rapport, tâches et indicateurs calculés (`metrics`) |
| `POST` | `/chat-assistant` | Chatbot de planification (`messages` : rôles `user` / `assistant`) |

---

<div id="workflow"></div>

> ### Guide d'Utilisation (Workflow)

**Trouver le partenaire idéal**
1. **Décrire l'idée de projet** dans la barre de recherche (ex. « réseau de transport optique pour pipelines pétroliers »), ou choisir une suggestion.
2. **Lire le classement** : le panneau *Partner Ranking* affiche les 19 partenaires avec leur pourcentage de correspondance ; les 3 meilleurs sont mis en évidence.
3. **Lire le diagnostic IA** des 3 meilleurs partenaires, qui s'écrit en temps réel sous chaque carte.
4. **Explorer un autre partenaire** : cliquer sur son nom dans le classement pour ouvrir sa fiche détaillée.
5. **Générer une proposition** : cliquer sur *Generate Partnership Proposal* pour obtenir une proposition B2B prête à copier.

**Préparer le suivi d'une réunion**
1. Ouvrir le **Meeting Assistant** depuis la barre de navigation.
2. Coller les notes de la réunion, puis cliquer sur *Analyze & Extract Corporate Assets*.
3. Consulter les indicateurs, le tableau des tâches et le rapport, le modifier si besoin, puis le copier.
4. Utiliser le **chatbot** pour planifier les prochaines étapes.

### Structure du Projet
```text
.
├── app.py                  # API FastAPI de la plateforme (port 8000)
├── index.html              # Interface : recherche, classement, fiches partenaires, propositions
├── seed_partners.py        # Insère les 7 partenaires de base + embeddings (sans doublons)
├── add_partners.py         # Ajoute 12 partenaires Huawei Tunisie (sans doublons)
├── supabase_setup.sql      # Création de la table, de pgvector et de la fonction match_partners
├── requirements.txt        # Dépendances Python de la plateforme
├── static/                 # Ressources publiques (logo.jpg, lp1.jpg)
├── .env                    # Variables secrètes (exclu de Git)
└── meeting-assistant/
    ├── app.py              # API FastAPI du Meeting Assistant (port 8001)
    ├── index.html          # Interface : analyse de réunion, indicateurs, chatbot
    ├── requirements.txt    # Dépendances Python du Meeting Assistant
    ├── static/             # Ressources publiques (logo.jpg, sp1.jpg)
    └── .vscode/            # Live Server configuré sur le port 5501
```

<div id="secu"></div>

> ### Sécurité

La protection des accès et des données repose sur les principes suivants :
* **Secrets isolés** : l'URL et la clé Supabase sont chargées depuis `.env`, jamais écrites dans le code ; `.env` est exclu du versioning via `.gitignore`.
* **Fichiers publics limités** : seul le dossier `static/` est servi publiquement ; le code source et `.env` ne sont pas accessibles depuis le navigateur.
* **Affichage sécurisé** : les données de la base et les textes générés par l'IA sont échappés avant d'être affichés (protection contre l'injection HTML / XSS).
* **CORS restreint** : les API n'acceptent que les requêtes provenant des pages Live Server (`5500`, `5501`).
* **Données fiables** : aucun indicateur n'est inventé ; les scores affichés sont calculés (similarité cosinus, indicateurs de réunion) et l'IA a pour consigne de ne pas inventer de chiffres.
* **Recommandation production** : activer le *Row Level Security (RLS)* sur la table `partner_profiles` avec des politiques de lecture, et utiliser une clé *secret* dédiée côté serveur.

<div id="conclusion"></div>

> ### Conclusion

Ce projet met en pratique l'intégralité d'un pipeline d'IA appliquée au métier : de la **vectorisation
sémantique** des idées de projet au **classement des partenaires** dans PostgreSQL/pgvector, jusqu'à la
**génération de diagnostics, de propositions et de comptes rendus de réunion** via Ollama. Le résultat
est une solution fonctionnelle, validée sur **19 partenaires Huawei de référence en Tunisie**, qui fait
gagner du temps aux équipes chargées des partenariats.

<div id="contacts"></div>

> ### Contact

* **Maram Bougossa** - [GitHub](https://github.com/YuuMii05)

---

<p align="right"><a href="#top">Retour au menu</a></p>
