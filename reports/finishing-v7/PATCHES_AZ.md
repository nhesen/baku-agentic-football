# V7: zərbə, geriyə ötürmə və keçid örtüyü

17 oktyabr 2026. Göndərilmiş `baku_fc_v7_patch.py` faylı hazır əvəzləmə kimi icra edilmədi. Faydalı fikirlər işləyən V6-nın üzərinə kiçik, ayrı yoxlanılan modullar kimi tətbiq edildi. Təklif faylının SHA-256 izi: `0a1ffa85b91414af6ae4c0b10de5755b63141892b2fa892e0464f69f7f815526`.

Bir qapıçı və dörd meydan oyunçusu saxlanılır. Mühərrik, fizika, atributlar və əmr adapteri dəyişdirilmir.

## Düzəlişlər

**Zərbə dəhlizi.** `finishing_tactics=shot` və ya `balanced` olduqda zərbə üçün minimum sahə oyunçusu boşluğu tələb edilir: 13 m-ə qədər 1.0 m, 22 m-ə qədər 1.8 m, daha uzaqda 2.5 m. Açıq uzaq zərbələrin əvvəlki 30 m həddi saxlanılır. Bu rəqəmlər qol ehtimalı modeli deyil, əvvəlcədən yazılmış həndəsi sınaq fərziyyəsidir. İcazə `shot_facts` daxilində daraldılır: zərbə həm offline ilk seçimdən, həm bütün model menyusundan çıxır; müstəqil validator da onu qəbul etmir.

**Cutback — cinahdan mərkəzə geriyə/yana ötürmə.** `cutback` və ya `balanced` rejimi yalnız açıq, qapıya daha yaxın mərkəzi qəbul nöqtəsini önə çəkir. Göndərən rəqib yarısının irəlisində və cinahda, qəbul edən mərkəzdə və qapıya ən azı 2 m daha yaxın olmalıdır; məsafə, açıq dəhliz, qəbul edənə təzyiq və geriyə irəliləyiş hədləri yoxlanılır. Belə pas 4 bal bonus alır və uyğun dəyərdə top sürmədən önə keçir. Dərin geri pas və ofsayd qadağaları saxlanılır; yalnız pas sayını artırmaq mükafatlandırılmır.

**Rəqib topu buraxdıqdan sonra qısa örtük yaddaşı.** `cover` və ya `balanced` rejimi görünən son rəqib sahibliyindən ən çox 1.5 saniyə sonra hərəkətli `LOOSE`/`UNKNOWN` top zamanı mövcud təhlükəli rəqib örtüyünü saxlayır. Bu, topun kimdə olduğunu uydurmur, zərbə/pasa icazə vermir. Öz pasımız, restart, matç/komanda dəyişməsi və vaxtın geriyə getməsi ilə qarışdırılmır. Bir toplayıcı ayrı qalır.

**Pas ehtimalı modelinin aktiv sxemə qoşulması.** `use_pass_model=true` artıq `flow` sxeminin pas sıralamasında da `retention()` çağırır. Əvvəl yalnız köhnə `legacy` yolu bunu edirdi. Modelin 7 xüsusiyyətinin miqyası və mənbə+çəki fingerprint-i saxlanır. Bu, pasdan sonra topun komandada qalmasını proqnozlaşdıran köhnə modeldir; yeni model öyrədilməyib. Bütün V7 nəticə matçlarında açar `false` saxlanılır. `optional-retention.json` ayrıca, matç üstünlüyü yoxlanmamış profildir.

## Saxlanılan qoruyucular

V6-nın görünən top sahibliyindən çıxan give-go yaddaşı, onun restart və UNKNOWN sıfırlamaları; qapıçı qoruması; pressdən əvvəl örtüklü yaxınlaşma; `delay_only`; öz pasının proyeksiyalı qəbul nöqtəsi; cooldown; ofsayd; qanuni restart götürən oyunçu və müstəqil əmr yoxlamaları saxlanılır.

Göndərilmiş patch-dəki bütöv `plan_five` və `enhance` əvəzləmələri tətbiq edilmir: onlar mövcud müdafiə və press qoruyucularını çıxarırdı. Yerli 2D mühərrikdə olmayan yuxarı/aşağı künc fərqi yaradılmır. Köhnə zərbə/qol sayından tək səbəb və ya yüksək xG nəticəsi çıxarılmır.

## Ayrı sınaq profilləri

- `finish-off.json`: V6-nın əvvəlki matç davranışı; yeni taktika yenilikləri söndürülüb.
- `finish-shot.json`: yalnız zərbə dəhlizi.
- `finish-cutback.json`: yalnız mərkəzə geriyə/yana ötürmə prioriteti.
- `finish-cover.json`: yalnız son rəqib buraxılışından sonra qısa örtük.
- `finish-balanced.json`: bu üç yeniliyin birgə sınağı.

Əsas yerli seçim `agentpitch-validated.json`, canlı yoxlanmamış AWS namizədi `aws-candidate.json` faylıdır. Əsas rejim əvvəlcədən yazılmış qəbul qaydasına və ayrıca yekun matçlara görə seçilir. Yeni variant bu qaydanı keçməsə V7-nin əsas profili V6 davranışını saxlayır; yeni xüsusiyyətlər ayrıca profillərdə mövcud olur.

## Yoxlamalar

11 yeni davranış testi: bloklu zərbənin bütün menyu və validatordan çıxması; açıq uzaq zərbənin qalması; cutback prioriteti və güzgü həndəsəsi; dərin geri pasın bonus almaması; opsional modelin həqiqətən çağırılması; rəqib buraxılışı yaddaşının bitməsi və sıfırlanması; öz pasının rəqib örtüyü sayılmaması; boş topda örtüyün saxlanması; restart/cooldown qoruyucuları. Oyun vaxtı olmayan payload-da örtüyün sonsuz saxlanmaması da yoxlanılır. Bunlar matç qələbə faizi deyil. Faktiki matç nəticələri `NETICELER_AZ.md` və `ALL_MATCHES.csv` fayllarında saxlanılır.
