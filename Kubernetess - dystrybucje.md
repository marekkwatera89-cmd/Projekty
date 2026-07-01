# Porównanie dystrybucji Kubernetes – K3s vs MicroK8s vs Vanilla Kubernetes

> Praktyczne porównanie trzech najpopularniejszych dystrybucji Kubernetes z uwzględnieniem wymagań sprzętowych, kosztów wdrożenia, czasu implementacji oraz zastosowań.

---

# Wstęp

Kubernetes stał się standardem w orkiestracji kontenerów. Wraz z jego rosnącą popularnością powstało wiele dystrybucji ułatwiających wdrożenie klastra. Najczęściej spotykane rozwiązania to:

- **Vanilla Kubernetes (kubeadm)** – oficjalna wersja rozwijana przez CNCF.
- **K3s** – lekka dystrybucja stworzona przez Rancher.
- **MicroK8s** – dystrybucja rozwijana przez Canonical.

Każda z nich posiada ten sam interfejs API Kubernetes, jednak różni się wymaganiami sprzętowymi, łatwością wdrożenia oraz kosztami utrzymania.

---

# Krótkie porównanie

| Cecha | Vanilla Kubernetes | K3s | MicroK8s |
|--------|-------------------|------|-----------|
| Trudność instalacji | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ |
| Zużycie pamięci RAM | Wysokie | Bardzo niskie | Średnie |
| Zużycie CPU | Średnie | Niskie | Średnie |
| Wdrożenie HA | Tak | Tak | Tak |
| Certyfikacja CNCF | Tak | Tak | Tak |
| Łatwość aktualizacji | Średnia | Bardzo łatwa | Łatwa |

---

# Vanilla Kubernetes 

## Czym jest?

Vanilla Kubernetes to oficjalna implementacja projektu Kubernetes. Nie zawiera dodatkowych komponentów ani uproszczeń. Administrator sam decyduje o wyborze wszystkich elementów klastra.

Najczęściej wykorzystywane narzędzia instalacyjne:

- kubeadm
- Kubespray
- Cluster API
- Talos Linux

---

## Zalety

### Pełna kontrola

Administrator wybiera:

- CNI (Calico, Cilium, Flannel)
- CSI
- Ingress Controller
- Storage
- Monitoring
- Logging
- Security

Nic nie jest narzucone.

---

### Standard rynkowy

Większość usług chmurowych bazuje właśnie na Vanilla Kubernetes:

- Amazon EKS
- Azure AKS
- Google GKE
- Oracle OKE

Znajomość Vanilla Kubernetes przekłada się na umiejętność pracy praktycznie z każdym klastrem produkcyjnym.

---

### Największa elastyczność

Możliwość zastosowania dowolnych rozwiązań:

- Ceph
- Longhorn
- NFS
- NGINX
- Cilium
- Prometheus
- Grafana
- Loki

---

## Wady

Największą wadą jest stopień skomplikowania.

Przy budowie klastra należy skonfigurować między innymi:

- etcd
- kube-apiserver
- scheduler
- controller-manager
- kubelet
- containerd
- Load Balancer
- Ingress
- Storage
- Certyfikaty

Budowa klastra produkcyjnego zajmuje zwykle od kilku dni do nawet tygodnia, w zależności od wymagań.

---

## Minimalne wymagania

Środowisko testowe

- 2 vCPU
- 4 GB RAM

Kontroler produkcyjny

- 4–8 vCPU
- 8–16 GB RAM

---

# K3s

## Czym jest?

K3s to lekka dystrybucja Kubernetes opracowana przez firmę Rancher.

Powstała z myślą o:

- Edge Computing
- IoT
- HomeLab
- Raspberry Pi
- małych i średnich klastrach produkcyjnych

Mimo uproszczeń pozostaje w pełni zgodna z Kubernetes i posiada certyfikację CNCF.

---

## Dlaczego K3s jest lekki?

Twórcy uprościli wiele komponentów.

Przykładowo:

- SQLite zamiast etcd (Single Node)
- Wbudowany Traefik
- Wbudowany ServiceLB
- Wbudowany Helm Controller

Instalacja sprowadza się praktycznie do jednego polecenia:

```bash
curl -sfL https://get.k3s.io | sh -
```

Po kilku minutach otrzymujemy działający klaster.

---

## Zalety

### Bardzo małe wymagania sprzętowe

Minimalne środowisko:

- 1 vCPU
- 1 GB RAM

Rekomendowane:

- 2 vCPU
- 2 GB RAM

Jest to nawet 3–4 razy mniej niż Vanilla Kubernetes.

---

### Szybkość wdrożenia

| Typ klastra | Czas |
|-------------|------|
| Single Node | 5 minut |
| HA | 20–30 minut |

---

### Niskie koszty

Dzięki niewielkim wymaganiom sprzętowym można:

- uruchomić więcej klastrów,
- wykorzystać mniejsze maszyny,
- znacząco obniżyć koszty chmury.

Przy kilkudziesięciu klastrach oszczędności mogą wynosić nawet kilkadziesiąt procent względem pełnego Kubernetes.

---

### Doskonały do Edge Computing

Idealnie sprawdza się w:

- sklepach
- oddziałach firmy
- fabrykach
- serwerowniach lokalnych
- urządzeniach IoT

---

## Wady

Domyślnie instalowane są dodatkowe komponenty (Traefik, ServiceLB), które w dużych środowiskach często są zastępowane rozwiązaniami enterprise.

Nie stanowi to jednak większego problemu.

---

# MicroK8s

## Czym jest?

MicroK8s jest rozwijany przez Canonical.

Największy nacisk położono na prostotę instalacji oraz integrację z Ubuntu.

Instalacja:

```bash
sudo snap install microk8s --classic
```

---

## Zalety

### Modułowa budowa

Dodatkowe komponenty można włączać poleceniami:

```bash
microk8s enable dns
microk8s enable ingress
microk8s enable storage
microk8s enable metallb
```

---

### Idealny dla programistów

MicroK8s świetnie sprawdza się jako lokalny klaster do:

- testów
- developmentu
- CI/CD
- Proof of Concept

---

### Integracja z Ubuntu

Jest bardzo dobrze wspierany przez Canonical.

---

## Wady

Największą wadą jest wykorzystanie pakietów Snap.

MicroK8s zużywa również zauważalnie więcej pamięci RAM niż K3s.

---

# Porównanie zużycia zasobów

Przybliżone zużycie zasobów przez pusty klaster.

| Dystrybucja | RAM | CPU |
|-------------|-----|-----|
| K3s | 500–800 MB | Bardzo niskie |
| MicroK8s | 1,5–2,5 GB | Średnie |
| Vanilla Kubernetes | 2–4 GB | Średnie |

Bezapelacyjnie wygrywa tutaj **K3s**.

---

# Czas wdrożenia

| Zadanie | Vanilla | K3s | MicroK8s |
|----------|----------|------|-----------|
| Instalacja Single Node | 1–2 godziny | 5 minut | 10 minut |
| Klaster HA | 1–3 dni | 20–30 minut | 1–2 godziny |
| Środowisko produkcyjne | kilka dni | kilka godzin | około 1 dnia |

Największą oszczędność czasu zapewnia K3s.

---

# Koszt wdrożenia

Przykład klastra składającego się z 3 maszyn.

| Dystrybucja | Zalecana VM | Koszt infrastruktury |
|-------------|------------|----------------------|
| K3s | 2 vCPU / 2 GB RAM | Niski |
| MicroK8s | 2 vCPU / 4 GB RAM | Średni |
| Vanilla Kubernetes | 4 vCPU / 8 GB RAM | Wysoki |

Do kosztów infrastruktury należy doliczyć czas administratora. W praktyce wdrożenie Vanilla Kubernetes wymaga znacznie większego nakładu pracy, co przekłada się na wyższy koszt projektu.

---

# Kiedy wybrać K3s?

K3s będzie najlepszym wyborem, gdy:

- liczy się szybkość wdrożenia,
- zasoby sprzętowe są ograniczone,
- budujemy HomeLab,
- tworzymy środowisko developerskie,
- wdrażamy rozwiązania Edge Computing,
- chcemy ograniczyć koszty infrastruktury,
- potrzebujemy wielu klastrów testowych.

---

# Kiedy wybrać MicroK8s?

MicroK8s warto wybrać gdy:

- pracujemy głównie na Ubuntu,
- potrzebujemy lokalnego klastra,
- tworzymy środowisko developerskie,
- chcemy szybko uruchomić Proof of Concept.

---

# Kiedy wybrać Vanilla Kubernetes?

Vanilla Kubernetes sprawdzi się najlepiej gdy:

- budujemy środowisko Enterprise,
- wymagamy pełnej kontroli nad komponentami,
- integrujemy zaawansowane rozwiązania sieciowe i storage,
- planujemy rozbudowane klastry produkcyjne,
- przygotowujemy się do certyfikatów CKA lub CKS.

---

# Architektura i wymagania infrastrukturalne

Jedną z największych różnic pomiędzy omawianymi dystrybucjami jest liczba wymaganych komponentów do zbudowania środowiska produkcyjnego.

## K3s

K3s został zaprojektowany z myślą o prostocie wdrożenia. Już pojedyncza maszyna wirtualna może pełnić rolę kompletnego klastra Kubernetes.

Minimalna architektura:

```
+----------------------+
|      VM 1            |
|----------------------|
| Control Plane        |
| Worker               |
| SQLite / etcd        |
| Traefik              |
| ServiceLB            |
+----------------------+
```

W praktyce oznacza to, że już **jedna maszyna wirtualna** pozwala uruchomić w pełni funkcjonalny klaster, który sprawdzi się w:

- środowiskach developerskich,
- laboratoriach,
- HomeLab,
- testach aplikacji,
- małych środowiskach produkcyjnych.

Jeżeli wymagamy wysokiej dostępności (HA), wystarczy rozbudować klaster do trzech serwerów.

```
Server 1
Server 2
Server 3
```

Bez konieczności instalowania wielu dodatkowych komponentów.

---

## MicroK8s

MicroK8s również umożliwia uruchomienie kompletnego klastra na pojedynczej maszynie.

```
+----------------------+
|      VM 1            |
|----------------------|
| Control Plane        |
| Worker               |
| Add-ons              |
+----------------------+
```

To rozwiązanie świetnie sprawdza się podczas:

- tworzenia środowisk testowych,
- nauki Kubernetes,
- lokalnego developmentu.

Podobnie jak K3s, w razie potrzeby można rozszerzyć klaster do konfiguracji wysokiej dostępności.

---

## Vanilla Kubernetes

W przypadku Vanilla Kubernetes sytuacja wygląda zupełnie inaczej.

Choć technicznie możliwe jest uruchomienie klastra na jednej maszynie, **nie jest to rozwiązanie zalecane ani spotykane w środowiskach produkcyjnych**. Standardem jest budowa architektury wysokiej dostępności (HA), która zapewnia odporność na awarie.

Typowa architektura produkcyjna obejmuje:

```
                 +-----------+
                 | HAProxy   |
                 +-----+-----+
                       |
        +--------------+--------------+
        |              |              |
+---------------+ +---------------+ +---------------+
| Control Plane | | Control Plane | | Control Plane |
|      #1       | |      #2       | |      #3       |
+---------------+ +---------------+ +---------------+
        |              |              |
        +--------------+--------------+
                       |
        +-------------------------------+
        |         Worker Nodes          |
        +-------------------------------+
                       |
               +---------------+
               | Storage (NFS, |
               | Ceph, SAN...) |
               +---------------+
```

Najczęściej wymagane są dodatkowe komponenty:

- 3 serwery Control Plane,
- Load Balancer (np. HAProxy lub Keepalived),
- współdzielona pamięć masowa (NFS, Ceph, SAN, Longhorn),
- Ingress Controller,
- cert-manager,
- rozwiązanie do monitoringu (Prometheus, Grafana),
- centralny system logowania (Loki, Elasticsearch, OpenSearch).

Powoduje to znacznie większą złożoność wdrożenia oraz wyższe koszty utrzymania.

---

## Przykładowe wymagania infrastrukturalne

| Element | K3s | MicroK8s | Vanilla Kubernetes |
|---------|-----|----------|--------------------|
| Minimalna liczba VM | **1** | **1** | **3–5** |
| Control Plane | 1 | 1 | 3 |
| Worker | opcjonalnie | opcjonalnie | osobne węzły |
| Load Balancer | Nie | Nie | Tak |
| HAProxy | Nie | Nie | Tak |
| NFS / Ceph | Opcjonalnie | Opcjonalnie | Zalecane |
| etcd | Wbudowane | Wbudowane | Osobna konfiguracja |
| Traefik / Ingress | Wbudowany | Add-on | Instalacja ręczna |

---

## Wpływ na koszt wdrożenia

Różnice w architekturze mają bezpośredni wpływ na koszt projektu.

Przykładowo:

**K3s**

- 1 maszyna wirtualna,
- około 15–30 minut instalacji,
- praktycznie brak dodatkowych komponentów.

**MicroK8s**

- 1 maszyna wirtualna,
- około 30–60 minut konfiguracji.

**Vanilla Kubernetes**

- minimum 3 maszyny dla Control Plane,
- osobne Workery,
- Load Balancer,
- magazyn danych (NFS, Ceph lub SAN),
- konfiguracja sieci,
- certyfikaty,
- monitoring,
- backup etcd.

W praktyce oznacza to, że wdrożenie produkcyjnego klastra Vanilla Kubernetes może wymagać **5–8 maszyn wirtualnych** oraz kilku dni pracy administratora, podczas gdy funkcjonalny klaster K3s lub MicroK8s można uruchomić na **jednej maszynie wirtualnej w ciągu kilkunastu minut**.

> **Uwaga:** Warto podkreślić, że możliwość uruchomienia K3s lub MicroK8s na jednej maszynie nie oznacza, że jest to zalecana architektura produkcyjna. W środowiskach wymagających wysokiej dostępności (HA) również dla tych dystrybucji rekomenduje się wykorzystanie co najmniej trzech serwerów kontrolnych. Jednak nawet w takiej konfiguracji liczba wymaganych komponentów i stopień skomplikowania pozostają zazwyczaj mniejsze niż w przypadku klasycznego Vanilla Kubernetes.


# Podsumowanie

Nie istnieje jedna najlepsza dystrybucja Kubernetes – wybór zależy od potrzeb organizacji.

| Zastosowanie | Najlepszy wybór |
|--------------|-----------------|
| HomeLab | 🥇 K3s |
| Edge Computing | 🥇 K3s |
| Raspberry Pi | 🥇 K3s |
| Małe środowiska produkcyjne | 🥇 K3s |
| Development | 🥇 MicroK8s |
| Ubuntu Desktop | 🥇 MicroK8s |
| Enterprise | 🥇 Vanilla Kubernetes |
| Chmura publiczna | 🥇 Vanilla Kubernetes |
| Nauka działania Kubernetes | 🥇 Vanilla Kubernetes |

## Wnioski

Jeżeli priorytetem są **niskie koszty, niewielkie zużycie zasobów oraz szybkie wdrożenie**, najlepszym wyborem będzie **K3s**. Pozwala uruchomić klaster w kilkanaście minut i znacząco ogranicza wymagania sprzętowe.

**MicroK8s** jest dobrym rozwiązaniem dla programistów oraz użytkowników Ubuntu, którzy potrzebują prostego środowiska testowego.

**Vanilla Kubernetes** pozostaje najlepszym wyborem dla **dużych** środowisk produkcyjnych i przedsiębiorstw, w których kluczowe są pełna kontrola nad konfiguracją, maksymalna elastyczność oraz zgodność z rozwiązaniami stosowanymi przez największych dostawców chmury.
