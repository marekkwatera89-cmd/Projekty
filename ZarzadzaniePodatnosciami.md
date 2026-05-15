# Wazuh, Nessus i DefectDojo – jak skutecznie zarządzać podatnościami

W środowiskach wirtualnych coraz częściej wykorzystuje się narzędzia takie jak Wazuh oraz Nessus do wykrywania podatności bezpieczeństwa, a następnie importuje wyniki do DefectDojo, gdzie można je centralnie analizować i śledzić proces ich naprawy.

## Import wyników do DefectDojo

DefectDojo pozwala na import wyników z wielu narzędzi, w tym z Wazuh oraz Nessus. Po imporcie otrzymujemy przejrzysty widok liczby podatności pogrupowanych według poziomu ryzyka.
<img width="1118" height="103" alt="obraz" src="https://github.com/user-attachments/assets/de2abef2-1b4e-4b6c-9f49-4effdf52819b" />

 

## Wazuh – analiza podatności na podstawie wersji kernela

Wazuh bardzo często opiera się na analizie wersji pakietów lub kernela systemu operacyjnego. Przykładowo, jeśli system posiada kernel w wersji `6.8.0-110`, Wazuh może automatycznie przypisać do niego wszystkie znane podatności związane z tą wersją według baz CVE/NVD.

W praktyce prowadzi to często do dużej liczby false positive. Dystrybucje Linux, takie jak Ubuntu od Canonical, stosują mechanizm backportingu poprawek bezpieczeństwa bez zmiany numeru wersji kernela. Oznacza to, że podatność może być już naprawiona, mimo że numer wersji nadal wygląda na podatny.

Na poniższym screenie Wazuh raportuje około 60 podatności typu Critical:

<img width="836" height="361" alt="obraz" src="https://github.com/user-attachments/assets/231a0bfb-73b6-4b6a-8b0c-da3599c576fe" />



Jednak po imporcie do DefectDojo widzimy już około 30 podatności Critical:
<img width="1059" height="121" alt="obraz" src="https://github.com/user-attachments/assets/1a0e4456-fc2c-469c-8508-7ab922964bf8" />

 
Różnica wynika głównie z deduplikacji podatności. Te same CVE mogą występować jednocześnie w dwóch kernelach, np.:

- `linux-image-6.8.0-110-generic`
- `linux-image-6.8.0-111-generic`

DefectDojo agreguje takie wpisy i nie pokazuje ich wielokrotnie. Dzięki temu raport staje się bardziej czytelny i łatwiejszy do analizy.

## Nessus – bardziej szczegółowy i dokładniejszy skan

Nessus wykonuje znacznie bardziej szczegółowy oraz rzetelny skan niż Wazuh. Oprócz samej wersji pakietów analizuje:

- konfigurację usług,
- odpowiedzi aplikacji,
- aktywne porty,
- możliwość realnego wykorzystania podatności,
- konfigurację systemu.

Dzięki temu liczba false positive jest zwykle mniejsza niż w przypadku Wazuh.

Dodatkową zaletą Nessusa jest możliwość wykonywania skanu uwierzytelnionego. Po połączeniu z systemem przez:

- login i hasło,
- SSH key,
- konto domenowe,
- WinRM (Windows),

Nessus może przeprowadzić bardzo dokładną analizę systemu operacyjnego i zainstalowanych pakietów.

W praktyce pozwala to wykrywać podatności znacznie dokładniej niż klasyczny skan sieciowy bez uwierzytelnienia.

## CVE, CVSS i EPSS

W analizie podatności warto rozróżniać trzy pojęcia:

| Termin | Znaczenie |
|---|---|
| CVE | Identyfikator podatności |
| CVSS | Poziom krytyczności (Low/Medium/High/Critical) |
| EPSS | Prawdopodobieństwo wykorzystania exploita |

Często zdarza się również, że różne źródła prezentują różne poziomy ryzyka dla tej samej podatności.

Przykład:

- Wazuh/NVD → Critical
- Canonical Ubuntu Security → Medium

Wynika to z faktu, że Canonical bierze pod uwagę rzeczywisty wpływ podatności na Ubuntu oraz zastosowane poprawki bezpieczeństwa.

## Dlaczego EPSS jest ważny

CVSS określa poziom krytyczności podatności, jednak nie mówi, czy podatność jest realnie wykorzystywana przez atakujących.

Przykład:

| CVE | CVSS | EPSS | Znaczenie |
|---|---|---|---|
| CVE-2024-XXXX | 9.8 Critical | 0.01 | Bardzo groźna technicznie, ale mało wykorzystywana |
| CVE-2024-YYYY | 6.5 Medium | 0.92 | Średnia krytyczność, ale aktywnie wykorzystywana |

Dlatego połączenie:

- CVSS,
- EPSS,
- danych vendorów (Canonical, RedHat),
- wyników Nessusa,
- wyników Wazuh,

daje znacznie lepszy obraz realnego ryzyka bezpieczeństwa.



## Automatyczne przypisywanie EPSS do podatności w DefectDojo

Aby lepiej oceniać ryzyko podatności, warto przypisywać do wyników również wskaźnik EPSS (Exploit Prediction Scoring System). Dzięki temu można określić prawdopodobieństwo realnego wykorzystania podatności przez atakujących.

W projekcie został dodany również skrypt Python, który:

- łączy się z API DefectDojo,
- pobiera listę podatności,
- odczytuje identyfikatory CVE,
- pobiera wynik EPSS z API FIRST,
- automatycznie aktualizuje podatności w DefectDojo.

Dzięki temu w DefectDojo można filtrować oraz priorytetyzować podatności nie tylko na podstawie CVSS, ale również realnego ryzyka exploita.

### Jak działa skrypt

1. Pobiera wszystkie aktywne podatności z DefectDojo.
2. Dla każdej podatności odczytuje numer CVE.
3. Łączy się z API EPSS:
4. Pobiera aktualny wynik EPSS.
5. Aktualizuje wpis w DefectDojo przez REST API.

### Skrypt, który użyłem w swojej pracy
[w załączniku](https://github.com/marekkwatera89-cmd/Projekty/blob/main/Pliki/eps-python.py)



## Podatności w IT nigdy nie „znikają”

Jednym z największych problemów bezpieczeństwa IT jest fakt, że raz przeanalizowane podatności nie dają pełnego spokoju. Środowisko IT stale się zmienia:

- pojawiają się nowe moduły kernela,
- instalowane są nowe pakiety,
- zmienia się konfiguracja systemu,
- dochodzą nowe zależności aplikacji.

Nawet jeśli dana podatność dziś wydaje się niegroźna lub niemożliwa do wykorzystania, za jakiś czas może stać się realnym zagrożeniem.

Dobrym przykładem są podatności :

- Dirty Frag
- Fragnesia,
- Copy Fail,
- błędy w sterownikach,
- podatności w modułach jądra.

Często exploit pojawia się dopiero wiele miesięcy po publikacji CVE.

## Aktualizacje zwiększają bezpieczeństwo, ale nie dają 100% ochrony

Regularne aktualizacje systemu operacyjnego, kernela oraz aplikacji znacząco zwiększają bezpieczeństwo środowiska i ograniczają ryzyko ataku.

Nie istnieje jednak 100% gwarancji bezpieczeństwa. W świecie cyberbezpieczeństwa zawsze mogą pojawić się:

- nowe podatności,
- exploity typu zero-day,
- błędy logiczne,
- nowe techniki obejścia zabezpieczeń.

Dlatego bezpieczeństwo powinno być traktowane jako ciągły proces monitorowania, analizy i aktualizacji systemów.
