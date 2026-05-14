# Wazuh, Nessus i DefectDojo – jak skutecznie zarządzać podatnościami

W środowiskach wirtualnych coraz częściej wykorzystuje się narzędzia takie jak Wazuh oraz Nessus do wykrywania podatności bezpieczeństwa, a następnie importuje wyniki do DefectDojo, gdzie można je centralnie analizować i śledzić proces ich naprawy.

## Import wyników do DefectDojo

DefectDojo pozwala na import wyników z wielu narzędzi, w tym z Wazuh oraz Nessus. Po imporcie otrzymujemy przejrzysty widok liczby podatności pogrupowanych według poziomu ryzyka.

![DefectDojo metrics](./DefectDojo_ap28_Wazuh.png)

## Wazuh – analiza podatności na podstawie wersji kernela

Wazuh bardzo często opiera się na analizie wersji pakietów lub kernela systemu operacyjnego. Przykładowo, jeśli system posiada kernel w wersji `6.8.0-110`, Wazuh może automatycznie przypisać do niego wszystkie znane podatności związane z tą wersją według baz CVE/NVD.

W praktyce prowadzi to często do dużej liczby false positive. Dystrybucje Linux, takie jak Ubuntu od Canonical, stosują mechanizm backportingu poprawek bezpieczeństwa bez zmiany numeru wersji kernela. Oznacza to, że podatność może być już naprawiona, mimo że numer wersji nadal wygląda na podatny.

Na poniższym screenie Wazuh raportuje około 60 podatności typu Critical:

![Wazuh vulnerabilities](./wazuh%2028.png)

Jednak po imporcie do DefectDojo widzimy już około 30 podatności Critical:

![DefectDojo Wazuh import](./DefectDojo_ap28_Nessus2.png)

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

## Podatności w IT nigdy nie „znikają”

Jednym z największych problemów bezpieczeństwa IT jest fakt, że raz przeanalizowane podatności nie dają pełnego spokoju. Środowisko IT stale się zmienia:

- pojawiają się nowe moduły kernela,
- instalowane są nowe pakiety,
- zmienia się konfiguracja systemu,
- dochodzą nowe zależności aplikacji.

Nawet jeśli dana podatność dziś wydaje się niegroźna lub niemożliwa do wykorzystania, za jakiś czas może stać się realnym zagrożeniem.

Dobrym przykładem są podatności typu:

- Dirty COW,
- Dirty Pipe,
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
