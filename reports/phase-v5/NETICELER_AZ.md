# V5 faza taktikalarının nəticələri

216 tam nəzarətli yerli matç: 4 təkrar yoxlama, 96 ilkin seçim, 36 ayrıca doğrulama və 80 toxunulmamış yekun oyun. Benchmark xətasının yoxlanması üçün 4 cütləşdirilmiş təkrar ilə cəmi 220 tamamlanmış cəhd var; əsas cədvələ eyni oyunun iki nüsxəsi daxil edilmir. R1 inteqrasiya pilotu bu saydan ayrıdır. Hər komanda bir GK və dörd meydan oyunçusu ilə başlayır.

## İlkin seçim

| Variant | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| t_wide | 12 | 3 | 6 | 3 | 3:3 | 25% |
| t_attack | 12 | 2 | 8 | 2 | 2:2 | 16.67% |
| t_complete | 12 | 0 | 11 | 1 | 0:1 | 0% |
| t_off | 12 | 0 | 11 | 1 | 0:1 | 0% |
| t_pivot | 12 | 0 | 11 | 1 | 0:1 | 0% |
| t_high | 12 | 0 | 9 | 3 | 0:3 | 0% |
| t_trigger | 12 | 0 | 9 | 3 | 0:3 | 0% |
| t_compact | 12 | 0 | 7 | 5 | 0:9 | 0% |

## Ayrıca doğrulama

| Variant | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| t_off | 12 | 4 | 6 | 2 | 5:3 | 33.33% |
| t_attack | 12 | 2 | 8 | 2 | 3:3 | 16.67% |
| t_wide | 12 | 0 | 10 | 2 | 1:3 | 0% |

Əvvəlcədən yazılmış qələbə → qol fərqi → vurulan qol qaydasına görə seçilən yeni variant: **t_attack**. Qələbə sayı bu dəfə ilkin seçim meyarıdır; bərabərlik çoxluğu təkbaşına qalib etmir.

## Yekun sınaq

| Variant / rəqib | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| t_off / baseline | 20 | 2 | 16 | 2 | 3:2 | 10% |
| t_attack / baseline | 20 | 4 | 13 | 3 | 4:3 | 20% |
| t_off / reference3 | 20 | 4 | 12 | 4 | 5:5 | 20% |
| t_attack / reference3 | 20 | 7 | 10 | 3 | 11:3 | 35% |

Yeni variant əvvəlcədən yazılan yekun qəbul şərtini keçdi; əsas profilə seçildi.

İki rəqib üzrə yeni–nəzarət qələbə faizi fərqi: 12.5 faiz bəndi; 10 cüt toxum üzrə bootstrap 95% intervalı: [-5.0, 30.0]. Bu, AWS turnirini qazanmaq ehtimalı deyil.

## Faktiki meydan göstəriciləri

**baseline: nəzarət → t_attack.** Zərbələr 70 → 95; geriyə ötürmələr 232 → 199; rəqibin son üçdəbirində sahiblik addımları 936 → 1183. Hücumda faktiki orta genişlik 14.53 → 17.78 m; müdafiədə 13.21 → 14.52 m. Bunlar frame-lərdən ölçülüb, yalnız nəzərdə tutulan hədəf nöqtələri deyil.

**reference3: nəzarət → t_attack.** Zərbələr 64 → 91; geriyə ötürmələr 162 → 143; rəqibin son üçdəbirində sahiblik addımları 804 → 1289. Hücumda faktiki orta genişlik 13.85 → 17.02 m; müdafiədə 13.09 → 14.18 m. Bunlar frame-lərdən ölçülüb, yalnız nəzərdə tutulan hədəf nöqtələri deyil.

## Sərhədlər

Bu, qaydalarla qurulan yeni taktika sistemidir; RL/PPO modeli təlim edilməyib. İki rəqib native baseline və arxiv V3-dür; Snow Halation FC və başqa AWS çempionlarının agentlərinə qarşı oyun yoxdur. Fizika, atributlar, əmr adapteri və roster eyni saxlanıb. Hər matç 1200 native tick-dir; canlı şəbəkə/model gecikməsi ölçülməyib.

Kodun `off` rejimi arxiv V3 ilə hər iki tərəfdə hadisə-bayt uyğunluğu yoxlamasını keçib. Yeni namizəd ilk seçimdən yekun sınağa qədər dəyişdirilməyib. Sınaq planı və mənbə izləri ayrıca fayllardadır. Ayrı mərhələlərdən faizləri model artımı kimi çıxmaq düzgün deyil.

`TAKTIKA_AZ.md` hər fazanın qaydasını və real futbol mənbələrini izah edir. `DIAGNOSTICS.json` faktiki mövqelənmə, hücum və taktika siqnalı saylarını verir. `RAW_MATCH_LOGS.zip` bütün 216 matçın hadisələrini saxlayır. Paket və build yerli hazırlanıb; AWS deploy edilməyib.

## Benchmark xətası və təkrar yoxlama

906 toxumlu yeni variantın bir oyununda native rəqib meydandan silinmiş top sahibinə müraciət edərək son 17 tick-də 85 callback xətası verdi. Rəqibin callback üçün aldığı snapshot surətində həmin köhnə ID təmizləndi; rəqibin mənbə kodu və native fizika dəyişdirilmədi. Həm nəzarət, həm yeni variant həmin toxumda hər iki tərəfdə təkrar oynadıldı. İlkin xətasız üç oyunun hadisələri bayt-bayt eyni qaldı. İlkin nəticələr silinməyib: `BENCHMARK_REPAIR.json` və xam arxivdə saxlanıb. Bu texniki düzəliş taktika sazlaması deyil. Əsas cədvəldə təkrarlar işlədilir və rəqib callback xətası yoxdur.
