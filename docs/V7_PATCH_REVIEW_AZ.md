# Göndərilmiş V7 patch-in V6 ilə müqayisəsi

17 oktyabr 2026. Yoxlanmış mənbə: GitHub commit `37750121f07c21db6b555f7844c51691ac652124`. Göndərilmiş Python faylı icra edilməyib; mətn və AST səviyyəsində oxunub. Mövcud V6 üzərində kiçik davranış ssenariləri və 7 kombinasiya testi işlədilib. Yeni matç seriyası keçirilməyib, qələbə artımı ölçülməyib. Əsas kod və profillər dəyişdirilməyib.

## Faydalı olanlar

| Mövzu | Yoxlama nəticəsi | Tövsiyə |
|---|---|---|
| Erkən uzaq zərbə | `early_shot=True` olduqda məsafə və yan bucaq icazəsi keçən zərbə, xətt bloklu olsa da ilk namizəd olur. Kod ssenarisində 25 m məsafə və 0.3 m xətt boşluğu ilə fallback `SHOOT` oldu. | Blok filtri və məsafəyə görə zərbə prioritetini ayrıca variant kimi sınamaq ən faydalı təklifdir. 12.5/17.5/22 m hədləri hələ əl ilə seçilmiş fərziyyələrdir. |
| Cinahdan mərkəzə geri/yana ötürmə — cutback | `progress > 3` irəli pasları önə çəkir. Açıq geriyə pas menyudan və validator icazəsindən tam silinmir. Ssenaridə −5 m irəliləyişli, açıq mərkəzi pas menyuda qaldı, ilk seçim isə `MOVE_TO` oldu. Təzyiq altında mövcud kod belə pası önə də çəkə bilər. | Açıq mərkəzi qəbul nöqtəsinə seçici bonus sınamağa dəyər. “Bütün geriyə paslar bloklanır” diaqnozu doğru deyil. |
| Rəqib pası havada olarkən örtük | Cari `cover()` yalnız `OPP` vəziyyətində markaj verir. `LOOSE`/`UNKNOWN` vaxtı, press edən oyunçudan başqa müdafiəçilərin hədəfi adi formaya qayıda bilər. | Son görünən rəqib sahibliyindən sonra qısa müddət markajın saxlanmasını ayrıca sınamaq faydalıdır. Hər naməlum topu rəqib sahibliyi saymaq olmaz; bir toplayıcı və öz pasımızın uçuş yaddaşı qorunmalıdır. |
| Öyrənilmiş pas modeli | Model faylı var, daxili validation AUC-si təxminən 0.800-dür. `legacy` yolunda istifadə edilir, aktiv `flow` sxeminin `attack.pass_menu()` funksiyasında çağırılmır. Eyni ssenaridə `use_pass_model` açarının dəyişməsi siyahını dəyişdirmədi. | Aktiv sxemə inteqrasiya ayrıca eksperiment ola bilər. Açarı sadəcə açmaq indiki `flow` davranışını dəyişmir. AUC pasdan sonra topun komandada qalmasını proqnozlaşdırır; qol və qələbə ehtimalı deyil. |

## Hazırkı koda uyğun olmayan diaqnozlar

1. **“give_go üçün yaddaş yoxdur” — yanlışdır.** [engine.py:98](https://github.com/nhesen/baku-agentic-football/blob/37750121f07c21db6b555f7844c51691ac652124/baku_fc/engine.py#L98) artıq görünən komanda daxili sahiblik keçidindən `last_passer` və `pass_age` yaradır. Match/komanda dəyişməsi, vaxtın geriyə getməsi, restart, rəqib və naməlum sahiblik üçün sıfırlama var. Mövcud 7 kombinasiya testi, o cümlədən ötürmədən sonra qaçış və yaddaşın sıfırlanması keçdi.
2. **“give_go blokunda təyin edilməmiş pt.y var” — hazırkı V6-da yoxdur.** [combinations.py:45](https://github.com/nhesen/baku-agentic-football/blob/37750121f07c21db6b555f7844c51691ac652124/baku_fc/combinations.py#L45) topun `y` koordinatını istifadə edir: `u,y=w.ball.x*w.sign,w.ball.y`, ardınca `y+dy*k` gəlir. `pt.y` yalnız dəyişənin təyin olunduğu üçbucaq dövründədir.
3. **“PRESS_BALL yoxdur, lookahead sabitdir” — yanlışdır.** [attack.py:183](https://github.com/nhesen/baku-agentic-football/blob/37750121f07c21db6b555f7844c51691ac652124/baku_fc/attack.py#L183) yaxınlıqda press əmri verir. Mövcud vaxt hesabı məsafə və top sürətindən asılıdır; öz pasımız üçün ayrıca trayektoriya proyeksiyası var. Ssenaridə yaxın press edən oyunçunun fallback-i `PRESS_BALL` oldu. Patch-in `dist/16` formulu da həqiqi kəsişmə vaxtını həll edən model deyil, başqa yaxınlaşma qaydasıdır.
4. **“Restart və cooldown qoruyucuları yoxdur” — yanlışdır.** [attack.py:171](https://github.com/nhesen/baku-agentic-football/blob/37750121f07c21db6b555f7844c51691ac652124/baku_fc/attack.py#L171) və [attack.py:194](https://github.com/nhesen/baku-agentic-football/blob/37750121f07c21db6b555f7844c51691ac652124/baku_fc/attack.py#L194) bunları saxlayır; müstəqil `commands.validate()` də top sahibliyini, cooldown-u və restart əmrini yoxlayır. Qapıçının boş topa yaxın çıxışı da var. Daha geniş süpürmə sahəsi mövcud davranışın alternatividir, çatışmayan bütün qoruyucuların bərpası deyil.

## Patch-i olduğu kimi köçürməməyin səbəbləri

- `enhance_v7()` yalnız hücum hissəsini qaytarır; mövcud `screen`/`combined` müdafiə qolunu daşımır. Tövsiyə etdiyi `combined` rejimində həmin ekran davranışını özü təmin etmir. Faylda ayrıca yeni `phase_coach` və ya `cover` funksiyası da yoxdur; buna görə rəqibin boş topu zamanı örtük problemi tam həll olunmayıb.
- `plan_five_v7()` mövcud “əvvəl örtüklü mövqedən yaxınlaş, sonra press et” sırasını və `delay_only` davranışını saxlamır. PRESS ilk seçildikdə bu, əvvəlki qaçıb-topa-atılma problemini geri gətirə bilər. Öz pasımız üçün proyeksiyalı qəbul nöqtəsi də çıxarılıb.
- Patch-in ötürmə yaddaşı mövcud yaddaşın restart/UNKNOWN sıfırlamalarını tam saxlamır. Hazır və işləyən yaddaşı bununla dəyişmək geriləmə riski yaradır.
- Native AgentPitch adapteri `TL` ilə `BL`-ni, `TR` ilə `BR`-ni eyni tərəfə çevirir: bu 2D sınaqda ayrıca yuxarı/aşağı künc üstünlüyünü ölçə bilmərik. Canlı AWS bu adları fərqli simulyasiya edirsə, ayrıca yoxlanmalıdır. Qapıçıdan uzaq tərəfə üstünlük mövcud `shot_facts()` daxilində artıq var.
- `high_xg_shot` adı kalibrə edilmiş xG modeli demək deyil. Patch uzaq/zəif zərbələri ilk seçimdən çıxarsa da, `clearance >= 1.4` olduqda yenidən menyuya əlavə edə bilir. LLM onu yenə seçə bilər; “yalnız sərt keyfiyyət həddi keçən zərbə” tələbi həm menyu, həm validator ilə uyğunlaşdırılmalıdır.
- `GK_DISTRIBUTE` ilə `PASS` yerli adapterdə eyni native pas hərəkətinə çevrilir. Əmrin adını dəyişmək burada təkbaşına yeni texnika və ya qələbə üstünlüyü yaratmır. Daha geniş qapıçı çıxışları mövcud validatorun qapıçı koordinat məhdudiyyətinə də uyğun gəlməlidir.
- “129 zərbədən 8 qolun birbaşa səbəbi budur” nəticəsi verilən rəqəmlərdən çıxmır. Bu, yoxlanmalı hipotezdir. Qapıçı, müdafiə, native fizika, paslar və təsadüfi matç hadisələri də nəticəyə təsir edir.
- `complete + combined + use_pass_model` açarlarını eyni anda aktivləşdirmək üçün ölçülmüş üstünlük yoxdur. Əvvəlki V6 `combined` sınağı `phase_tactics=attack` ilə idi və 12 oyunda 1Q/8H/3M aldı; patch-in təklif etdiyi dəqiq yeni paket hələ ölçülməyib. Başqa konfiqurasiyanın nəticəsini bu paketə köçürmək olmaz.

## Prioritet

Birinci namizəd: **bloklu uzaq zərbənin ilk seçim olmasını azaltmaq**. İkinci namizəd: **açıq cutback prioriteti**. Üçüncü: **son görünən rəqib pası zamanı qısa örtük yaddaşı**. Bunlar ayrıca və sonra birlikdə eyni toxum/rəqiblərlə yoxlanmalıdır. Pas ehtimalı modeli isə qol məqsədini üstələməyən ayrıca variant olmalıdır. İşləyən give-go yaddaşı, press yaxınlaşması, restart və cooldown qoruyucuları saxlanmalıdır.

Bu baxış V7-nin qələbə faizini artırdığını təsdiqləmir; hansı hissələrinin yeni sınağa dəyərli olduğunu müəyyən edir. Təkrarlana bilən kod ssenarilərinin faktları `REVIEW_PROBES.json`, 7 testin çıxışı `current-give-go-tests.txt` faylındadır.
