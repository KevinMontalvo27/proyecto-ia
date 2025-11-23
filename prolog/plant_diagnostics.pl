:- use_module(library(odbc)).
:- use_module(library(process)).
:- dynamic planta_tiene/2.
:- dynamic umbral_sensor/4. %umbral_sensor(sensor, plant_type, min, max)

% ------------------------------
% CONEXIÓN A BASE DE DATOS
% ------------------------------
connect_db :-
    odbc_connect('PostgreSQL35W', _Conn,
        [ user('postgres'),
          password('admin123'),
          alias(pgdb),
          open(once)
        ]).

% ------------------------------
% CARGA DE HECHOS DINÁMICOS
% ------------------------------
cargar_plantas :-
    connect_db,
    retractall(planta_tiene(_, _)),  % Limpia hechos previos
    forall(
        odbc_query(pgdb,
            'SELECT plant, diagnostic FROM plant_health',
            row(Plant, Diagnostic)),
        assertz(planta_tiene(Plant, Diagnostic))
    ),
    odbc_disconnect(pgdb).

% ============================================================
% CARGAR UMBRALES DE SENSORES DESDE BD
% ============================================================
cargar_umbrales :-
    connect_db,
    retractall(umbral_sensor(_, _, _, _)),
    forall(
        odbc_query(pgdb,
            'SELECT sensor, plant_type, umbral_min, umbral_max FROM sensor_data',
            row(Sensor, PlantType, Min, Max)),
        assertz(umbral_sensor(Sensor, PlantType, Min, Max))
    ),
    odbc_disconnect(pgdb),
    write('Umbrales cargados'), nl.


% ============================================================
% REGLA: Temperatura (enciende SOLO si está ALTA), predicados sobrecargados, el -Min es un prefijo que dice que no se usara la variable
% ============================================================
sensor_fuera_de_rango(temperatura, PlantType, Valor, Resultado) :-
    umbral_sensor(temperatura, PlantType, _Min, Max),
    (Valor > Max
     -> Resultado = true   % ALTA → ENCIENDE abanico
    ; Resultado = false    % BAJA o Normal → APAGA
    ).

% ============================================================
% REGLA: Humedad (enciende solo si está BAJA)
% ============================================================
sensor_fuera_de_rango(humedad, PlantType, Valor, Resultado) :-
    umbral_sensor(humedad, PlantType, Min, _Max),
    (Valor < Min
     -> Resultado = true   % BAJA → ENCIENDE bomba
    ; Resultado = false    % ALTA o Normal → APAGA bomba
    ).

% ============================================================
% REGLA: Luz (retorna estado para Gemini), aqui es un XD, el como se usara esta chingadera
% ============================================================
sensor_luz_estado(luz, PlantType, Valor, Estado) :-
    umbral_sensor(luz, PlantType, Min, Max),
    (Valor < Min
     -> Estado = low_light   % BAJA → Recomendación: aumentar luz
    ; Valor > Max
     -> Estado = high_light  % ALTA → Recomendación: reducir luz
    ; Estado = normal        % Normal → Sin recomendación
    ).


% ------------------------------
% LLAMAR SCRIPT PYTHON
% ------------------------------
activar_sistema(Planta, Diagnosticos) :-
    format('Activando sistema para ~w. Enfermedades detectadas: ~w~n',
           [Planta, Diagnosticos]),
    atomics_to_string(Diagnosticos, " ", DiagStr),
    % Ejecuta el script Python con los argumentos
    process_create(
        path(python),
        ['actuador.py', Planta, DiagStr],
        [cwd('C:/Users/Dell/Documents/Prolog')]  %CAMBIAR RUTA SI ES NECESARIO
    ).

% ------------------------------
% REGLAS   PARA CONSULTAS EXTERNAS
% ------------------------------
check_planta(Planta, Diagnostico, Respuesta) :-
    planta_tiene(Planta, Diagnostico),      % Verifica que exista ese diagnóstico
    Diagnostico \= healthy,                 % Solo si no es healthy
    activar_sistema(Planta, [Diagnostico]), % Llama al script
    format(string(Respuesta), "Alerta activada para ~w: ~w", [Planta, Diagnostico]).

% Si la planta está sana
check_planta(Planta, healthy, Respuesta) :-
    format(string(Respuesta), "~w está saludable, no se activa alerta.", [Planta]).

% ============================================================
% INICIALIZAR TODO EL SISTEMA
% ============================================================
inicializar_sistema :-
    write('Inicializando Prolog...'), nl,
    cargar_plantas,
    write('Plantas cargadas'), nl,
    cargar_umbrales,
    write('Sistema listo para consultas'), nl.

% ============================================================