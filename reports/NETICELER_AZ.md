# Düzülüş sınağının nəticələri — 17 oktyabr 2026

276 tam yerli matç: 4 təkrar-yoxlama, 144 ilkin seçim, 48 ayrıca doğrulama, 80 yekun sınaq. Hər tərəfdə GK daxil **5 oyunçu**. Heç bir canlı LLM və AWS matçı yoxdur.

## İlkin seçim

| Sxem | Oyun | Q | H | M | Qollar | Xal | Qələbə |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2-1-1 | 16 | 2 | 13 | 1 | 3:1 | 19 | 12.5% |
| 1-2-1 | 16 | 3 | 10 | 3 | 3:3 | 19 | 18.75% |
| 1-3 | 16 | 3 | 9 | 4 | 4:5 | 18 | 18.75% |
| 1-1-2 | 16 | 3 | 9 | 4 | 3:5 | 18 | 18.75% |
| 1-1-1-1 | 16 | 1 | 14 | 1 | 1:1 | 17 | 6.25% |
| original | 16 | 3 | 8 | 5 | 3:6 | 17 | 18.75% |
| 2-2 | 16 | 1 | 13 | 2 | 1:2 | 16 | 6.25% |
| 4-0 | 16 | 1 | 10 | 5 | 1:5 | 13 | 6.25% |
| 3-1 | 16 | 0 | 12 | 4 | 0:4 | 12 | 0% |

## Ayrı doğrulama

| Sxem | Oyun | Q | H | M | Qollar | Xal | Qələbə |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2-1-1 | 16 | 1 | 15 | 0 | 1:0 | 18 | 6.25% |
| original | 16 | 1 | 13 | 2 | 1:2 | 16 | 6.25% |
| 1-2-1 | 16 | 2 | 10 | 4 | 2:4 | 16 | 12.5% |

Seçim əvvəlcədən yazılmış 3Q+H, qol fərqi və native rəqibə qarşı xalın azalmaması qaydasına görə edildi. **2–1–1** seçildi, native fingerprint `6fb9b2ff5963e591`. Qələbə faizinin mütləq artması seçim meyarı deyildi. Sınaq dəsti seçildikdən sonra kod dəyişdirilmədi.

## Toxunulmamış yekun oyunlar

| Versiya / rəqib | Oyun | Q | H | M | Qollar | Xal | Qələbə |
|---|---:|---:|---:|---:|---:|---:|---:|
| Əvvəlki V3 / baseline | 20 | 4 | 15 | 1 | 5:1 | 27 | 20% |
| 2–1–1 / baseline | 20 | 0 | 20 | 0 | 0:0 | 20 | 0% |
| Əvvəlki V3 / reference3 | 20 | 2 | 16 | 2 | 2:2 | 22 | 10% |
| 2–1–1 / reference3 | 20 | 1 | 16 | 3 | 3:5 | 19 | 5% |

Yekun oyunlarda zəifləmə aşkarlandığı üçün əsas təqdimat profilində əvvəlki V3 hücum davranışı saxlandı (`formation: original`, 1–1–2-yə yaxın mobil quruluş). 2–1–1 ayrıca eksperimental profildə saxlanıb. Bu, testdən sonra parametr sazlaması deyil, zəif namizədin geri qaytarılmasıdır. Yeni versiyanı qələbə artımı kimi təqdim etmirik.

Native rəqibə qarşı bu yekun dəstdə qələbə sayı artmadı. Daha yüksək qələbə faizi əldə etdiyimizi iddia etmirik.
Native qələbə faizi fərqi -20 faiz bəndi; cütləşdirilmiş 10 toxum üzrə bootstrap 95% intervalı [-45.0, 0.0]. Bu interval yalnız həmin yerli rəqib və oyun seçiminə aiddir; AWS yarışını qazanmaq ehtimalı deyil.

## Nə öyrəndik?

2–1–1-in irəli çıxması ilkin seçimdə məğlubiyyətlərin azalmasına əsaslanır. 1–2–1 bəzi oyunlarda daha çox qələbə verdi, lakin ayrıca doğrulamada daha çox qol buraxdı. 3–1 və sadələşdirilmiş 4–0 bu parametr dəstində zəif nəticə verdi; bu, bütün mümkün 3–1/4–0 sistemlərinin zəif olması demək deyil.

Mövqe həndəsəsi təkbaşına problemi həll etmir. `DIAGNOSTICS.json` topla irəliləmə, geriyə/irəli ötürmələr, qəbul edilmiş zərbələr və qol nəticəsini göstərir. Həmin göstəricilər ölçüldü, optimallaşdırma mükafatı kimi oyun nəticəsinin yerinə qoyulmadı.

Sxemlər hərəkətli dəstək nöqtələridir. İlk GK/DEF/MID/MID/FWD rosteri, atributlar, tək pressçi, fərdi örtük, ötürmə və zərbə qaydaları sabitdir. 4–0-da ayrıca mobil arxa örtük var. Bu sınaq yalnız portalın başlanğıc düzülüş seçimini dəyişən sınaq deyil.

## Hücum niyə zəiflədi?

Eyni 20 native rəqib matçında əvvəlki V3-dən 2–1–1-ə keçəndə geriyə ötürmələr **213 → 373**, rəqibin son üçdəbirində topa sahib olduğumuz müşahidə addımları **908 → 175**, qəbul edilmiş zərbə əmrləri **71 → 17** oldu. Topa sahiblik addımları **9557 → 10840** artsa da, qollar **5 → 0** düşdü. Bu, həmin rəqibə qarşı daha çox top saxlamağın hücum təhlükəsini artırmadığını göstərir; təkcə sxemin adından səbəb çıxarmırıq.

Seçimdə `3Q+H` xalı bərabərlikləri mükafatlandırdığı üçün müdafiəçi 2–1–1 irəli çıxdı. İstifadəçinin əsas hədəfi qələbə faizidir. Növbəti seçimdə ilkin meyar yeni rəqib dəstində qələbə sayı olmalı, qol buraxma və bərabərlik sayı əlavə göstərici kimi izlənməlidir. Bu qayda hazırkı yekun nəticəni yenidən seçmək üçün geriyə tətbiq edilmədi.

Əvvəlki hesabatda native rəqibə qarşı V3 20 oyundan 1-ni (5%) qazanmışdı. Buradakı **4/20 (20%) başqa toxumlardakı eyni əvvəlki davranışdır**, modelin 5%-dən 20%-ə yaxşılaşdırılması deyil. Kiçik dəstlərin dəyişkənliyini göstərir. 2–1–1 qalib elan edilmədi; əsas profilə əvvəlki davranış qaytarıldı.

## Fayllar və təkrar etmək

`ALL_MATCHES.csv/jsonl`: bütün nəticələr. `RAW_MATCH_LOGS.zip`: hər matçın meta/hadisələri, işlədilən namizəd və arxiv rəqib mənbələri, manifestlər. `REPLAY_INDEX.json`: ilk oyun, varsa ilk qələbə və ilk məğlubiyyətin mənbə uyğunluğu. Bərabərlik və məğlubiyyətlər gizlədilməyib.

Runner workspace-də əvvəlki iki paket və native repo ilə işləyir: `BAKU_STUDY_CANDIDATE` yeni mənbə qovluğunu göstərməlidir. `selection-plan.json` toxumları və müqayisə qaydasını saxlayır. Çıxış qovluqları fərqli kodla təkrar istifadə edilməməlidir.

## AWS üçün sərhəd

`baku-football-v4/profiles/agentpitch-validated.json` 100×60 yerli meydanda sınaqdan keçmiş offline konfiqurasiyadır. `aws-candidate.json` və əsas settings 110×70, LLM aktiv namizəddir; canlı AWS-də yoxlanmayıb və başqa fingerprint-ə malikdir. Beş Runtime yerli qurulub, deploy edilməyib. Komanda kodu və real payload gələndə koordinatlar, əmr enumları, gecikmə və modelin menyu seçimi rəsmi mühitdə ayrıca ölçülməlidir.

Yeni xarici mənbələr və video baxış sərhədləri `ARASDIRMA_AZ.md` daxilindədir.
