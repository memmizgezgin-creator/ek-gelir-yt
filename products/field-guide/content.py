"""Content of 'From Stellite to PCD', the cutting tool materials field guide. build.py renders it."""

TITLE = "From Stellite to PCD"
SUBTITLE = "A field guide to cutting tool materials: where each one came from, what it does at the edge, and when it is still the right choice."
BRAND = "Lost Tool Archive"
EDITION = "Edition 1, 2026"

INTRO = [
    "Every cutting tool material in your tool crib was once the newest, fastest thing in the shop. Each one arrived because the one before it hit a wall: the edge got too hot, the work got too hard, or the machine got faster than the tool. Knowing that history is not nostalgia. It tells you what each material is good at, where it fails, and why a 120 year old idea like cobalt alloy or high-speed steel still earns its place next to coated carbide and CBN.",
    "This guide walks through the materials in the order they arrived. For each one you get the story in a few lines, what it is made of, how hot the edge can run, typical starting speeds, where it still wins today and where it does not. The last pages put everything side by side and give a short selection routine you can use at the machine.",
    "It is brand neutral on purpose. Grades and trade names change; the physics of hot hardness, toughness and chemical wear does not.",
]

TIMELINE = [
    ("1740s", "Benjamin Huntsman's crucible steel gives Sheffield reliable carbon tool steel."),
    ("1868", "Robert Mushet's self-hardening tungsten steel hardens in air and roughly doubles cutting speed."),
    ("1900", "Taylor and White show high-speed steel at the Paris Exposition, cutting with the tool red hot."),
    ("1907", "Elwood Haynes patents cobalt-chromium alloys later sold as Stellite."),
    ("1926", "Krupp sells sintered tungsten carbide as Widia, \"wie Diamant\"."),
    ("1930s", "Titanium and tantalum carbides make carbide usable on steel; molybdenum high-speed steels appear."),
    ("1950s", "Alumina ceramic inserts reach production; GE makes synthetic diamond (1954) and cubic boron nitride (1957)."),
    ("1969", "First CVD coated carbide inserts; Borazon CBN sold as an abrasive."),
    ("1970s", "Polycrystalline diamond and CBN tool blanks; TiCN cermets from Japan."),
    ("1980s", "PVD TiN coatings, whisker-reinforced and SiAlON ceramics."),
    ("Today", "Multilayer PVD/CVD coatings, nano-grain carbide, powder-metal HSS, PCD and CBN as standard production tools."),
]

# Hot hardness: approximate temperature where the edge loses useful hardness.
MATERIALS = [
    {
        "name": "Carbon tool steel",
        "era": "Crucible steel 1740s, dominant until about 1870",
        "comp": "Iron with 0.6 to 1.4 % carbon, water or oil quenched",
        "hot": "About 200 to 250 °C",
        "vc": "Steel: about 5 to 10 m/min",
        "story": "For more than a century every lathe tool, file and chisel was plain carbon steel, forged and quenched by the toolmaker himself. It takes a keen edge and is easy to make, but it tempers back as soon as it gets hot. The practical speed limit of every machine in the early industrial age was really the temperature limit of this steel.",
        "today": ["Woodworking, hand tools, scrapers, punches and some form tools for soft materials", "Teaching: the cheapest way to show what heat does to an edge"],
        "not": ["Any production metal cutting: it softens long before HSS would even notice"],
    },
    {
        "name": "Self-hardening (Mushet) steel",
        "era": "1868 to about 1900",
        "comp": "High carbon steel with about 7 to 9 % tungsten and 2 % manganese, hardened in air",
        "hot": "Higher than carbon steel, about 300 to 400 °C",
        "vc": "Steel: roughly 1.5 to 2 times carbon steel",
        "story": "Robert Mushet found that tungsten and manganese made a steel that hardened by itself as it cooled in air. He never patented it and kept the recipe secret, selling it through Samuel Osborn in Sheffield. It was the first alloy tool steel and the direct ancestor of high-speed steel.",
        "today": ["None in production. Its idea, alloying for hardness at temperature, lives on in every HSS grade"],
        "not": ["Replaced completely by HSS after 1900"],
    },
    {
        "name": "High-speed steel (HSS)",
        "era": "1900 to today",
        "comp": "Tungsten (T grades) or molybdenum (M grades) steels with chromium and vanadium; cobalt grades such as M35 and M42; powder metal (PM) grades for finer carbides",
        "hot": "About 550 to 650 °C",
        "vc": "Steel: about 20 to 40 m/min uncoated, more with TiN or TiAlN coating",
        "story": "Frederick Taylor and Maunsel White heat treated tungsten steel far hotter than anyone dared, close to melting. At the 1900 Paris Exposition their tools cut steel while glowing. The name stuck: high-speed. Molybdenum grades replaced much of the tungsten from the 1930s, and powder metallurgy made HSS tougher and more uniform.",
        "today": ["Taps, drills, reamers, broaches, gear hobs and form tools where toughness and a sharp, regrindable edge matter more than speed", "Small machines and low spindle speeds, interrupted cuts, older equipment", "Tools that are ground to a special profile in-house"],
        "not": ["High speed turning or milling of steel and cast iron: carbide is 4 to 10 times faster", "Hardened materials above about 45 HRC"],
    },
    {
        "name": "Cast cobalt alloys (Stellite type)",
        "era": "Patented 1907, important as a cutting material from about 1915 to the 1940s",
        "comp": "Cobalt base with about 25 to 35 % chromium, 4 to 20 % tungsten and 1 to 3 % carbon; cast, not heat treated",
        "hot": "Holds hardness to around red heat, about 700 to 800 °C",
        "vc": "Steel: historically above HSS, roughly 1.25 to 2 times",
        "story": "Elwood Haynes, a car pioneer in Kokomo, Indiana, made a cobalt alloy that would not rust and stayed hard when hot. As a tool bit it outran high-speed steel and fed the shell lathes of the First World War. Cemented carbide took the cutting job from the 1930s, but the alloy moved into wear and heat applications and never left.",
        "today": ["Hardfacing of valve seats, turbine and pump parts, saw tips for wood", "Some knife and wear applications where corrosion and heat resistance count", "As a cutting tool: niche, mostly historical"],
        "not": ["General cutting today: lower hardness and toughness than modern carbide grades"],
    },
    {
        "name": "Cemented carbide",
        "era": "1926 to today, the default production tool material",
        "comp": "Tungsten carbide grains bonded with cobalt (typically 3 to 15 %); steel grades add titanium, tantalum or niobium carbides; ISO groups P, M, K, N, S, H",
        "hot": "About 800 to 1000 °C (coating dependent)",
        "vc": "Steel: about 100 to 200 m/min uncoated, about 150 to 400 m/min coated",
        "story": "Karl Schröter at Osram sintered tungsten carbide with cobalt to make wire drawing dies. Krupp sold it in 1926 as Widia. Early grades cratered quickly on steel until titanium and tantalum carbides were added in the 1930s. Coatings from 1969 on turned the insert into an engineered system: substrate for toughness, coating for heat and chemical wear.",
        "today": ["Almost all turning, milling and drilling in production, from steel to superalloys", "Solid carbide end mills and drills; brazed tips for special tools", "Choose by ISO group first, then by toughness versus wear resistance"],
        "not": ["Finishing hardened steel above about 55 HRC at high speed (CBN)", "High speed aluminium finishing where PCD lasts many times longer"],
    },
    {
        "name": "Cermets",
        "era": "First TiC-Ni versions 1930s; practical TiCN grades from Japan in the 1970s",
        "comp": "Titanium carbonitride based hard phase with nickel and cobalt binder",
        "hot": "High, low tendency to weld to steel",
        "vc": "Steel finishing: about 150 to 400 m/min at light depths",
        "story": "Cermets were developed to be carbide's harder, more chemically stable cousin. They struggled with toughness for decades, then found their place in finishing, where low built-up edge and excellent surface finish matter more than heavy cuts.",
        "today": ["Finishing and semi finishing of steel and stainless with stable setups", "When surface finish and size control over a long run matter"],
        "not": ["Heavy roughing, interrupted cuts, unstable setups", "Titanium and nickel alloys"],
    },
    {
        "name": "Ceramics",
        "era": "Alumina inserts 1950s; mixed, whisker-reinforced and SiAlON grades 1980s",
        "comp": "Aluminium oxide (white), alumina with TiC (black or mixed), SiC whisker reinforced alumina, silicon nitride and SiAlON",
        "hot": "About 1200 °C and above",
        "vc": "Cast iron: about 300 to 1000 m/min; nickel alloys (SiAlON, whisker): about 150 to 400 m/min",
        "story": "Ceramics promised speeds no metal-bonded tool could survive, but early inserts chipped as soon as a cut was interrupted. Whisker reinforcement and silicon nitride based grades made them tough enough for production, especially on cast iron and heat resistant superalloys.",
        "today": ["Grey cast iron turning and milling at very high speed (silicon nitride)", "Roughing Inconel and other nickel alloys (SiAlON, whisker)", "Hard turning in stable conditions (mixed alumina)"],
        "not": ["Aluminium, titanium, soft steel", "Wet cutting with thermal shock on some grades, weak machines and long overhangs"],
    },
    {
        "name": "Cubic boron nitride (CBN, PCBN)",
        "era": "Synthesized by GE 1957; Borazon 1969; PCBN tool blanks from the 1970s",
        "comp": "Polycrystalline CBN, high content grades for interrupted cuts and cast iron, low content grades with ceramic binder for hardened steel",
        "hot": "Stable to about 1300 °C and chemically inert to iron",
        "vc": "Hardened steel 55 to 65 HRC: about 100 to 250 m/min",
        "story": "CBN is the second hardest material after diamond and, unlike diamond, it does not react with iron. That made hard turning possible: finishing hardened gears, bearings and shafts on a lathe instead of a grinder.",
        "today": ["Hard turning of steel above about 45 to 50 HRC", "Powder metal parts, chilled and grey cast iron at high speed", "Sintered and hardfaced parts, including Stellite overlays"],
        "not": ["Soft steel: it wears faster than carbide there", "Aluminium and non ferrous work (PCD is the choice)"],
    },
    {
        "name": "Polycrystalline diamond (PCD) and diamond coatings",
        "era": "Synthetic diamond 1954; PCD tool blanks 1970s; CVD diamond coatings 1990s",
        "comp": "Diamond grains sintered with cobalt on a carbide backing; CVD diamond films on carbide",
        "hot": "Limited to about 700 °C, and it reacts with iron",
        "vc": "Aluminium alloys: about 500 to 3000 m/min and more",
        "story": "Natural diamond tools were used for centuries on soft materials, but only synthetic diamond made them affordable and consistent. PCD changed automotive aluminium machining and composites, where it can outlast carbide by a factor of 10 to 100.",
        "today": ["High silicon aluminium, copper, brass, graphite, composites (CFRP, GFRP), wood based panels", "Long production runs where tool changes cost more than the tool"],
        "not": ["Steel, cast iron, nickel and titanium alloys: carbon diffuses into the work and the edge disappears"],
    },
]

COMPARE_HEAD = ["Material", "Hot hardness", "Toughness", "Typical work today", "Starting speed (steel unless noted)"]
COMPARE = [
    ["Carbon tool steel", "About 200 °C", "High", "Wood, hand tools", "5 to 10 m/min"],
    ["HSS / PM-HSS", "About 600 °C", "Very high", "Taps, drills, form tools", "20 to 40 m/min"],
    ["Cast cobalt (Stellite)", "About 750 °C", "Medium", "Hardfacing, wear parts", "Historical"],
    ["Carbide, coated", "About 900 °C", "Medium to high", "General production", "150 to 400 m/min"],
    ["Cermet", "High", "Medium", "Steel finishing", "150 to 400 m/min"],
    ["Ceramic", "About 1200 °C", "Low", "Cast iron, nickel alloys", "Cast iron 300 to 1000 m/min"],
    ["CBN / PCBN", "About 1300 °C", "Low to medium", "Hardened steel, cast iron", "Hard steel 100 to 250 m/min"],
    ["PCD", "About 700 °C", "Low to medium", "Aluminium, non ferrous, composites", "Aluminium 500 to 3000 m/min"],
]

SELECTION = [
    ("1. What is the work material?", "Steel, stainless, cast iron, non ferrous, heat resistant alloy or hardened steel. This is the ISO P, M, K, N, S or H group, and it removes half the list at once. Iron based work rules out PCD; soft steel rules out CBN."),
    ("2. How hard is it?", "Above about 45 to 50 HRC, CBN or mixed ceramic. Below that, carbide or cermet."),
    ("3. Is the cut continuous or interrupted?", "Interruptions, scale and unstable clamping favour tough materials: HSS, tough carbide grades, high content CBN. Brittle ceramics and cermets want a stable, continuous cut."),
    ("4. What limits you: speed, finish, or tool life?", "Finishing pass on steel: cermet or a sharp PVD carbide. Long runs in aluminium: PCD. Speed on cast iron: ceramic or CBN."),
    ("5. What can the machine do?", "A small or old machine that cannot reach the speed a material needs will make that material wear worse, not better. HSS and uncoated or PVD carbide are forgiving at low speeds."),
]

DISCLAIMER = "Speeds and temperatures are typical starting ranges from published handbook and supplier data, for orientation only. Always start from the tool maker's recommendation for the exact grade, then adjust on the machine."

ABOUT = "Lost Tool Archive is a documentary channel about forgotten machines and the history of cutting tools, made by a cutting tools specialist. Watch the stories behind these materials on YouTube: Stellite, Mushet steel, high-speed steel and more."
