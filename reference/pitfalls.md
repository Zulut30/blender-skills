# Blender pitfalls
Журнал известных граблей при работе с Blender Python API через MCP `execute_blender_code`. Пополнять при обнаружении новых случаев.

## KeyError 'Principled BSDF' в нодах материала
**Симптом:** `KeyError: 'Principled BSDF'` при `mat.node_tree.nodes['Principled BSDF']`.
**Причина:** UI пользователя в `ru_RU`, имя ноды в дереве отображается локализованным («Principled BSDF» становится «Принципиальный BSDF» и т.п.) при включённом переводе datablock-имён.
**Фикс:** искать ноду по типу, а не по имени: `next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')`.

## KeyError 'Camera' при доступе к камере сцены
**Симптом:** `bpy.data.objects['Camera']` бросает KeyError, хотя камера в сцене есть.
**Причина:** при `use_translate_new_dataname=True` имя камеры по умолчанию переведено («Камера»).
**Фикс:** использовать `bpy.context.scene.camera` вместо доступа по имени: `cam = bpy.context.scene.camera`.

## Default cube называется «Куб» в ru_RU
**Симптом:** `bpy.data.objects['Cube']` не находится; новые примитивы тоже создаются с переведёнными именами.
**Причина:** `bpy.context.preferences.view.use_translate_new_dataname=True` переводит имена создаваемых датаблоков.
**Фикс:** всегда переименовывать сразу после создания: `bpy.ops.mesh.primitive_cube_add(); obj = bpy.context.active_object; obj.name = 'MyCube'; obj.data.name = 'MyCubeMesh'`.

## BLENDER_EEVEE_NEXT не существует в 5.1
**Симптом:** `scene.render.engine = 'BLENDER_EEVEE_NEXT'` падает с TypeError на enum.
**Причина:** в Blender 5.1 движок называется просто `BLENDER_EEVEE` (NEXT существовал в 4.2-4.x как переходное имя, в 5.x его убрали/переименовали обратно).
**Фикс:** проверять enum перед присвоением: `valid = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]; scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in valid else valid[0]`.

## Объект визуально нужного размера, но bbox/scale неправильный
**Симптом:** geometry nodes / физика / экспорт ведут себя так, будто объект другого размера; `obj.dimensions` не совпадает с визуалом.
**Причина:** установили `obj.scale = (...)`, но не применили трансформацию — scale остался множителем поверх mesh-данных.
**Фикс:** после изменения scale делать `bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)` (объект должен быть selected+active).

## select_all бросает RuntimeError из-за контекста
**Симптом:** `bpy.ops.object.select_all(action='SELECT')` → `RuntimeError: Operator bpy.ops.object.select_all.poll() failed, context is incorrect`.
**Причина:** оператор требует валидного контекста (object mode, корректная area). В headless / при неподходящем mode poll проваливается.
**Фикс:** обходить операторы напрямую через API: `for o in bpy.context.scene.objects: o.select_set(True)`. Перед mode-зависимыми операторами проверять `bpy.context.mode == 'OBJECT'`.

## bmesh индексный доступ падает после изменений топологии
**Симптом:** `bm.verts[i]` или `bm.faces[i]` бросает IndexError или возвращает мусор после `bm.verts.new()` / удаления.
**Причина:** внутренняя lookup-таблица bmesh не обновляется автоматически при изменениях.
**Фикс:** вызывать `bm.verts.ensure_lookup_table()` (и аналогично для `edges`/`faces`) после любой модификации топологии перед индексным доступом.

## Рендер сохраняется не туда, куда указали
**Симптом:** указали `filepath`, но файла там нет / он пустой; реальный PNG лежит в temp.
**Причина:** `render_viewport_to_path` (и часть рендер-операторов) пишут во временную директорию и возвращают фактический путь в результате вызова.
**Фикс:** читать поле `filepath` из ответа MCP-вызова, не доверять переданному пути: `result = render_viewport_to_path(...); actual = result['filepath']`.

## EEVEE samples: eevee vs eevee_next property group
**Симптом:** `scene.eevee.taa_render_samples = N` падает с AttributeError, или наоборот `scene.eevee_next` не существует.
**Причина:** между 4.x и 5.x менялась группа свойств EEVEE (в 4.2+ был `eevee_next`, в 5.1 каноничный — `eevee`, но в зависимости от сборки могут различаться).
**Фикс:** try по обоим: `ee = getattr(scene, 'eevee_next', None) or scene.eevee; ee.taa_render_samples = 64`.

## Локальные python-переменные не переживают вызов
**Симптом:** во втором `execute_blender_code` ссылка `obj` из первого вызова — `NameError`, или указывает на что-то странное.
**Причина:** каждый вызов `execute_blender_code` — это новый `exec` namespace. Сохраняется только состояние Blender (`bpy.data`).
**Фикс:** между вызовами адресоваться к данным только через `bpy.data.objects['MyName']` / `bpy.context.scene.camera` и т.п. Имена давать явные и стабильные.

## materials.append копит дубликаты при повторе скрипта
**Симптом:** при повторном запуске одного и того же setup-скрипта у меша 2, 3, N копий одного материала; рендер использует не тот слот.
**Причина:** `mesh.materials.append(mat)` не идемпотентен — каждый запуск добавляет ещё один слот.
**Фикс:** перед append очищать слоты, если переустанавливаем: `mesh.materials.clear(); mesh.materials.append(mat)`. Либо проверять наличие: `if mat.name not in mesh.materials: mesh.materials.append(mat)`.

## World nodes: Background есть, но эффекта нет / KeyError
**Симптом:** `world.node_tree` равен None и падает AttributeError, либо изменения в `nodes['Background']` не отражаются на рендере.
**Причина:** у world по умолчанию могут быть выключены ноды (`use_nodes=False`), тогда `node_tree` == None. Имена встроенных нод (Background, Output) — английские внутренние идентификаторы, они НЕ локализуются.
**Фикс:** `world = bpy.context.scene.world; world.use_nodes = True; bg = world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1.0)`.

## auto_frame отдалён, главный объект — крошка в кадре
**Симптом:** `auto_frame(...)` корректно вычисляет bbox, но рендер выдаёт огромный фон/пол и крошечный целевой объект.
**Причина:** в список переданы помещение-сцена объекты (большой ground plane, skybox-прокси), которые расширяют bbox далеко за пределы объекта интереса.
**Фикс:** передавать в `auto_frame` только объекты-«герои» (без ground, без больших backdrop). Шаблон `arch_building.py` делает это через отдельный `frame_targets`. Альтернатива — уменьшить ground (10×10 вместо 60×60).

## Сырые primitive_*_add без хелпера: имя локализовано, scale не применён
**Симптом:** `obj` после `bpy.ops.mesh.primitive_torus_add(...)` именуется «Тор» в ru_RU, а его scale остаётся неединичным после ручной установки `obj.scale = ...`.
**Причина:** хелперы `add_*` единственное место, где имя задаётся явно и scale применяется автоматически. Сырые операторы этого не делают.
**Фикс:** для torus есть `H.add_torus`. Если оператор не покрыт — сразу после `bpy.context.object`: `obj.name = "..."; obj.data.name = "..."; obj.scale = (...); _apply_scale(obj)`.

## Повторные auto_frame порождают SkillCamera.001/.002 и раздувают bbox
**Симптом:** второй и последующий вызовы `auto_frame(...)` (или `frame_camera`) ставят камеру очень далеко; рендер показывает крошечную сцену.
**Причина:** `frame_camera` создавал новую камеру `SkillCamera`, существующая `SkillCamera` оставалась → Blender авторенеймил в `.001`, `.002`. Потом `bbox_of` на «всех объектах» подхватывал frustum старых камер и тащил их позицию в bbox → радиус кадра огромный → дистанция огромная.
**Фикс:** `frame_camera` (helpers v1.0.1) удаляет все предыдущие `SkillCamera*` перед созданием новой. `bbox_of` фильтрует тип `MESH/CURVE/SURFACE/META/FONT` и игнорирует камеры/лайты. При построении сцены передавай в `auto_frame` явный список mesh-объектов.

## Composite-helper parenting удваивает мировые координаты детей
**Симптом:** `add_gargoyle((x, y, z))` или похожий composite-helper создаёт root Empty в (x,y,z) И помещает детей в (x,y,z); после parent-set дети оказываются в (2x, 2y, 2z).
**Причина:** `child.parent = root` без сброса локальных координат → world = parent_world @ child_local; если child_local уже = world coord, всё умножается.
**Фикс (helpers v1.1.0):** `add_gargoyle` теперь строит детей в локальных оффсетах от (0,0,0) и в самом конце делает `root.location = target`. Тот же паттерн применяй ВО ВСЕХ собственных composite-helpers: build at origin → parent → translate root. Альтернатива: использовать `child.matrix_parent_inverse = root.matrix_world.inverted()` при parent-set.

## EEVEE world Volume Scatter поглощает свет → чёрный рендер
**Симптом:** после `add_volumetric_fog(density=0.01)` вся сцена становится чёрной даже на средних дистанциях.
**Причина:** в EEVEE Next World Volume рассчитывается агрессивно по большим дистанциям; при большой камере (≥80 м) и density>0.005 оптическая глубина перекрывает почти всё излучение; при low-strength sky сцена темнеет до 0.
**Фикс:** для близких сцен density 0.003–0.008. Для дальних кадров — пропорционально меньше или вовсе без world volume (используй Object volume в локальном объёме). Перед рендером всегда делай test-render с `density=0` чтобы убедиться, что освещение в принципе работает.

## `view_transform` в Blender 5.x: AgX по умолчанию, Filmic может отсутствовать
**Симптом:** `set_filmic_high_contrast()` не выставляет 'Filmic' — остаётся 'AgX'.
**Причина:** в Blender 4.x был добавлен AgX как новый дефолт; в 5.1 Filmic всё ещё доступен, но порядок enum может отличаться. Кроме того, чтение `enum_items` через `bl_rna.properties['view_transform']` иногда возвращает только `['NONE']` в скриптовом контексте (нестабильное поведение API).
**Фикс:** AgX даёт хороший результат и не требует переключения; принимай его как валидный default. Если нужен именно Filmic — попробуй `vs.view_transform = 'Filmic'` напрямую в try/except, не полагаясь на enum_items.

## execute_blender_code timeout на огромных скриптах
**Симптом:** `mcp__Blender__execute_blender_code` возвращает `MCP error -32001: Request timed out`; Blender перестаёт отвечать на следующие вызовы.
**Причина:** один скрипт, создающий >300 объектов за один вызов (особенно `paving_stones` сеткой + множество torch'ей с light datablocks + tower_windows с рамками и т.д.) выходит за MCP timeout. После этого MCP сервер залипает в очереди.
**Фикс:**
- Чанкуй большие сцены: сначала экстерьер → render preview, потом интерьер → render preview, потом атмосфера. Каждый chunk 50-150 объектов.
- Большие сетки (paving_stones >400 плиток) разбивай на квадранты и в отдельные вызовы.
- После таймаута связь с Blender нужно восстанавливать вручную (пользователь перезапускает аддон/Blender).
- Для частых рендеров отдельных мелких объектов используй `add_*` хелперы напрямую, а не template-style большой скрипт.

## paving_stones для больших площадей: дорого, использует material.copy() per tile
**Симптом:** `paving_stones((-13.5,-13.5),(13.5,1.0), tile_size=0.8, color_jitter>0)` создаёт ~600 кубов и столько же копий материала — таймаут MCP, очень медленный рендер.
**Причина:** color_jitter создаёт `material.copy()` для каждой плитки, чтобы варьировать цвет. Это очень тяжело по datablocks.
**Фикс:**
- Для больших площадей (>10×10м) используй один большой `add_plane` с `procedural_stone(bumpiness=0.6)` — voronoi даёт визуальное впечатление швов между блоками.
- Применяй настоящий `paving_stones` только для маленьких декоративных участков (5×5м или меньше) у камеры.
- Для длинной дорожки используй несколько крупных `add_cube` с jitter позиции, не сетку плиток.
- Если нужен paving_stones большой — поставь `color_jitter=0` (один материал на всё).

## Blender 5.x Slotted Actions: `action.fcurves` removed
**Симптом:** `AttributeError: 'Action' object has no attribute 'fcurves'` при попытке настроить интерполяцию ключей через `cam.animation_data.action.fcurves`.
**Причина:** в Blender 4.4+/5.x введён Slotted Actions API. F-curves теперь живут под `action.layers[0].strips[0].channelbag(slot).fcurves`, где slot — `action.slots[0]`.
**Фикс:** проверь оба пути:
```python
a = cam.animation_data.action
fcurves = a.fcurves if hasattr(a, 'fcurves') else None
if fcurves is None and hasattr(a, 'slots'):
    slot = a.slots[0]
    fcurves = a.layers[0].strips[0].channelbag(slot).fcurves
```
Helper `keyframe_camera_path` в скилле уже поддерживает оба пути (legacy + slotted).

## Bezier overshoots between widely-spaced orbit keyframes
**Симптом:** при облёте камеры ключевые кадры A → B → C дают траекторию, которая «вылетает» далеко за пределы орбиты — на промежуточных кадрах объект совсем не виден.
**Причина:** Bezier с auto-clamped handles интерполирует за пределы прямой линии между точками если угловой шаг между соседними ключами >60°. Один прыжок N → SW = ~135° приводит к камере в (-50, 5, 27) на середине пути.
**Фикс:**
- Распределяй orbit-ключи с шагом ≤45° (т.е. 8 ключей на полный круг для гладкой бесшовной).
- ИЛИ используй `bezier_orbit_keyframes` helper — он гарантирует равномерное распределение.
- ИЛИ переключись на `LINEAR` интерполяцию для orbit-сегмента.
- Всегда render preview промежуточных кадров (середин между keys) до полного render — это поймает overshoot за один render-цикл, а не за полные 144 кадра.

## Render всей анимации одним вызовом таймаутит MCP
**Симптом:** `bpy.ops.render.render(animation=True)` через `execute_blender_code` блокирует MCP на много минут → таймаут.
**Фикс:** рендери покадрово в Python-цикле:
```python
for i in range(start, end+1):
    scn.frame_set(i)
    scn.render.filepath = f"{out_dir}/frame_{i:04d}.png"
    bpy.ops.render.render(write_still=True)
```
Чанкуй по 20–30 кадров на вызов `execute_blender_code` (5–10 минут на чанк). После всех чанков — собирай mp4 через ffmpeg на хост-машине.
Helper `render_animation_frames` в скилле делает это правильно (per-frame, без `animation=True`).

## ShaderNodeTexSky: NISHITA отсутствует в Blender 5.1 — есть только Hosek-Wilkie/Preetham
**Симптом:** `sky.sky_type = 'NISHITA'` бросает enum error; хелпер `set_sunset_world` доходит до fallback без неба.
**Причина:** в 5.1 ShaderNodeTexSky предлагает `SINGLE_SCATTERING / MULTIPLE_SCATTERING / PREETHAM / HOSEK_WILKIE` — Nishita появится только в 5.2/5.3.
**Фикс:** для физически-корректного неба в 5.1 используй `HOSEK_WILKIE`. Параметры:
```python
sky.sky_type = 'HOSEK_WILKIE'
sky.sun_direction = (cos(elev)*cos(azim), cos(elev)*sin(azim), sin(elev))
sky.turbidity = 2.5  # 2..4 ясно, 6+ хмуро
sky.ground_albedo = 0.30
```
Линкуй `sky.outputs[0] → background.inputs['Color']`.

## Procedural-облака как emissive plane: видны только если plane в FOV И не блокируется CloudCeiling-плоскостью
**Симптом:** добавленный cloud plane не виден на рендере, хотя материал создан.
**Причина:** plane может быть выше FOV камеры (z=80, при камере z=20-30 и горизонтальном взгляде — за пределами кадра); либо `blend_method='BLEND'` в EEVEE даёт корректную прозрачность только если облака смотрят в камеру.
**Фикс:**
- Для cinematic shot: 4-6 разбросанных tilted-планов на разных x/y/z вокруг центра сцены, размер 80-100м, угол наклона 10-20°.
- Установить материал в `blend_method='BLEND'`, `shadow_method='NONE'`.
- Material: TexCoord(Generated) → Mapping → 2× Noise (разные scale) → multiply → ColorRamp → MixShader(Transparent + Emission).
- Альтернатива: VolumeScatter с density driven Noise — но в EEVEE дорого и часто чёрный (см. pitfall 21).

## Setting object origin to hinge for door/drawbridge animation
**Симптом:** `obj.rotation_euler.x = math.radians(-85)` крутит объект вокруг его центра, а не вокруг петли — мост улетает в небо.
**Причина:** rotation работает вокруг origin'а объекта; по умолчанию у `add_cube` origin = центр меша.
**Фикс:** перед keyframing — переустанови origin к точке петли:
```python
bpy.context.scene.cursor.location = (0, -15, 0.06)  # координата петли
for o in bpy.context.scene.objects: o.select_set(False)
db.select_set(True); bpy.context.view_layer.objects.active = db
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
```
После этого rotation_euler поворачивает вокруг петли. Применимо к воротам, ставням, мечу, висящим знамёнам.

## Sun direction → sky AND scene SUN object должны совпадать
**Симптом:** небо показывает закат с одного направления, а тени на замке падают как от другого солнца — сцена визуально диссонирует.
**Причина:** `sky.sun_direction` управляет ТОЛЬКО внешним видом неба; SUN-light-object даёт направленный свет на сцену независимо.
**Фикс:** после установки `sky.sun_direction = (dx, dy, dz)` синхронизируй SUN object:
```python
sun.location = (dx*40, dy*40, dz*40)
direction = mathutils.Vector((0,0,5)) - sun.location
sun.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
```
Это даёт когерентность: тени и блики идут от того же направления, что и яркая точка солнца на небе.

## Bird-like cinematic flight: 12+ keyframes + AUTO_CLAMPED + roll
**Паттерн (не баг):** для плавного полёта типа «птица» 6-8 ключей недостаточно — между ними bezier overshoot или прямые отрезки. Минимум 12-14 keyframes для 8-секундного шота.
- Используй AUTO_CLAMPED handles на location + rotation_euler.
- Добавляй небольшой Z-banking (1-12°) на orbit-сегментах через `Quaternion(direction, math.radians(roll)) @ track_quat`.
- Сегменты: descent → orbit (4-6 точек по углу ≤45°) → straighten → approach → entry → reveal.
- Финальный кадр должен пулнуть назад от ближайшего обьекта на 2-3м, иначе клиппинг.

## Pitfall 29: Geometry Nodes на 5.x — node_group через bpy.data, не через operator
**Симптом:** `RuntimeError: poll() failed` или `context is incorrect` при попытке добавить GN модификатор через `bpy.ops.node.new_geometry_nodes_modifier()` или похожие операторы.
**Причина:** Operator-based создание GN-tree требует UI-context (открытый Geometry Nodes editor), которого через MCP `execute_blender_code` нет.
**Фикс:** Создавай node group чисто через data API:
```python
ng = bpy.data.node_groups.new('MyGN', 'GeometryNodeTree')
# add nodes via ng.nodes.new('GeometryNodeXxx'), wire with ng.links.new(...)
mod = obj.modifiers.new('Nodes', 'NODES')
mod.node_group = ng
```
Хелперы `gn_scatter_on_surface`, `gn_array_along_curve`, `gn_random_transform` уже это делают.

## Pitfall 30: bpy.ops.import_scene.obj устарел в Blender 3.3+
**Симптом:** `RuntimeError: Operator bpy.ops.import_scene.obj poll failed` или `AttributeError: Calling operator "bpy.ops.import_scene.obj" error, could not be found`.
**Причина:** Старый OBJ импортёр заменён на новый в 3.3+. Нужен `bpy.ops.wm.obj_import(filepath=...)`.
**Фикс:** Используй helper `import_obj()` или напрямую `bpy.ops.wm.obj_import(filepath=path)`. Для FBX оператор остался: `bpy.ops.import_scene.fbx`.

## Pitfall 31: Cloth simulation в MCP даёт rest pose / scatter_grass_tufts с count > 500 таймаутит
**Симптом:** (a) `bpy.ops.ptcache.bake_all()` или `bpy.ops.cloth.bake()` зависает MCP (требует UI). (b) `scatter_grass_tufts(count=600)` таймаутит на raycast loop.
**Причина:** (a) Cloth bake — UI-операция, blocks the MCP socket. (b) Per-vertex raycasting в питоновском цикле — O(N) проход, при N=600 идёт >MCP timeout.
**Фикс:** (a) Используй ShapeKey-based static deformation (как в `add_curtain` — синусоидальная волна по вершинам, без симуляции). (b) Cap count ≤300 на один вызов `scatter_grass_tufts`. Для 600 — два вызова с разными seed.

## Pitfall 32: Decimate с ratio<0.1 ломает manifold
**Симптом:** После `decimate_mesh(obj, ratio=0.05)` последующие boolean операции выдают `Solver could not find a solution` или дают inverted normals.
**Причина:** Decimate COLLAPSE удаляет рёбра агрессивно — при ratio<0.1 мелкие фичи коллапсируют в self-intersecting/non-manifold геометрию.
**Фикс:**
- Перед apply: `assert len(obj.data.polygons) > 4`.
- После apply: `bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.remove_doubles(threshold=1e-4); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')`.
- Для бульев лучше ratio>=0.2.

## Pitfall 33: hdri_world с Windows-путями молчаливый black world
**Симптом:** `hdri_world(r'C:\hdris\sunset.hdr')` отрабатывает без exception, но мир чёрный на рендере.
**Причина:** `bpy.data.images.load()` иногда не парсит обратные слэши в путях на Windows и возвращает «загруженный» image объект без пиксельных данных. Проверки нет.
**Фикс:**
- Передавай только raw-string или forward-slashes: `r"C:\path\to.hdr"` или `"C:/path/to.hdr"`.
- Helper `hdri_world` нормализует путь через `path.replace('\\\\', '/')` и проверяет `image.has_data`. Если `has_data=False` — поднимает понятный exception.
- Тест: после загрузки — `print(image.size)`. Размер (0, 0) → файл не считан.

## Pitfall 34: Зачитывание `obj.bound_box` сразу после операторов даёт устаревшие координаты
**Симптом:** `auto_frame([obj])` после `boolean_difference` или `transform_apply` фреймит на старый bbox; place_on_floor роняет объект под землю.
**Причина:** `obj.bound_box` lazily пересчитывается при следующем view_layer evaluate. Сразу после оператора — кешированные данные.
**Фикс:** Перед чтением `bound_box` явно вызови `bpy.context.view_layer.update()` или (надёжнее) `obj.evaluated_get(bpy.context.evaluated_depsgraph_get())`. Хелпер `bbox_of` делает это.

## Pitfall 35: Linked / library-override объекты неизменяемы
**Симптом:** при открытии `.blend` со ссылками на отсутствующие пути появляются "ghost" объекты с `obj.library is not None`; хелперы, итерирующие `bpy.data.objects`, падают с `AttributeError: read-only property` при `materials.append` / `obj.scale = ...`.
**Причина:** linked / override datablocks иммутабельны со стороны зависящего файла.
**Фикс:**
```python
for o in list(bpy.data.objects):
    if o.library is not None:
        continue  # skip linked
# или сделать всё локальным:
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.make_local(type='ALL')
```

## Pitfall 36: `transform_apply` на multi-user mesh data
**Симптом:** `RuntimeError: cannot apply to a multi user data` при `bpy.ops.object.transform_apply(scale=True)` на примитиве, который шарит mesh с другим объектом (часто после duplicate-linked).
**Причина:** apply transform мутирует mesh; multi-user mesh data — общий.
**Фикс:**
```python
if obj.data.users > 1:
    obj.data = obj.data.copy()
bpy.ops.object.transform_apply(scale=True)
```

## Pitfall 37: Повторный `scene.collection.objects.link()` бросает RuntimeError
**Симптом:** хелпер создаёт объект и линкует его в scene collection; на втором запуске — `RuntimeError: Object 'Foo' already in collection`.
**Причина:** объект уже залинкован прошлым вызовом; хелперы должны дедуплицировать.
**Фикс:**
```python
coll = bpy.context.scene.collection
if obj.name not in coll.objects:
    coll.objects.link(obj)
```
Применяй этот паттерн в любом composite-хелпере, который создаёт Empty/light и пере-линкует их.

## Pitfall 38: EEVEE viewport vs render samples расходятся
**Симптом:** превью в viewport выглядит шумно или гладко, а финальный рендер — наоборот; разные пайплайны сэмплинга.
**Причина:** `scene.eevee.taa_samples` (viewport) и `scene.eevee.taa_render_samples` (render) независимы; `set_render` трогает только render-сторону.
**Фикс:** при подготовке финального рендера ставь оба для консистентности:
```python
for attr in ('eevee_next', 'eevee'):
    if hasattr(scene, attr):
        grp = getattr(scene, attr)
        if hasattr(grp, 'taa_render_samples'): grp.taa_render_samples = N
        if hasattr(grp, 'taa_samples'):        grp.taa_samples = max(N // 4, 8)
```

## Pitfall 39: Cycles GPU молча сваливается на CPU
**Симптом:** `scene.cycles.device = 'GPU'` проходит, но рендер в 10 раз медленнее ожидаемого — фактически работает CPU.
**Причина:** в user preferences также должны быть выставлены device-type и per-device enable list; одного флага сцены недостаточно.
**Фикс:**
```python
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'  # или 'CUDA' / 'HIP' / 'METAL' / 'ONEAPI'
prefs.refresh_devices()
for d in prefs.devices:
    d.use = d.type != 'CPU'
scene.cycles.device = 'GPU'
```
На Windows + NVIDIA предпочтительнее OPTIX; если недоступен — fallback на CUDA. На macOS — METAL.

## Pitfall 40: `modifier_apply` падает на скрытых объектах
**Симптом:** `bpy.ops.object.modifier_apply(modifier='Subdivision')` возвращает `CANCELLED` без traceback, когда target скрыт во вьюпорте.
**Причина:** poll оператора требует, чтобы объект был visible И active; скрытые объекты не проходят poll.
**Фикс:**
```python
was_hidden = obj.hide_get()
obj.hide_set(False)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.modifier_apply(modifier=mod_name)
obj.hide_set(was_hidden)
```

## Pitfall 41: `transform_apply(scale=True)` молча сносит shape keys
**Симптом:** меши с shape keys (face morphs, custom normals на ригах) теряют все ключи после apply scale; визуал "схлопывается" к base shape.
**Причина:** apply scale пере-печёт mesh; дельты shape-key хранятся относительно base mesh и не могут быть пере-печены через `transform_apply`.
**Фикс:**
- Применяй scale ДО добавления shape keys, ИЛИ
- Используй Mesh Data Transfer / Lattice modifier вместо scale, ИЛИ
- Сохрани shape-key offsets, примени scale, пересоздай ключи со скейленными offsets:
```python
keys = [(k.name, [v.co.copy() for v in k.data]) for k in obj.data.shape_keys.key_blocks] \
       if obj.data.shape_keys else []
# ... apply scale ...
# ... rebuild keys, multiplying each saved co by the scale factor ...
```
Хелперы вроде `add_cube` безопасны — они применяют scale до того, как существуют ключи. Актуально только при скейлинге уже-keyed мешей (например, импортированных персонажей).
