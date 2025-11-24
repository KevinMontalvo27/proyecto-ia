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
          password('123456789'),
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

% Caso 1: Diagnóstico registrado en BD y NO es healthy
check_planta(Planta, Diagnostico, Respuesta) :-
    planta_tiene(Planta, Diagnostico),      % Verifica que exista en la BD
    Diagnostico \= healthy,                 % Solo si no es healthy
    format(string(Respuesta), "Alerta: ~w detectado en ~w. Se recomienda intervencion inmediata.", [Diagnostico, Planta]).

% Caso 2: Planta está sana
check_planta(Planta, healthy, Respuesta) :-
    format(string(Respuesta), "~w está saludable. No se requiere accion.", [Planta]).

% Caso 3: Diagnóstico NO registrado en la BD (nuevo diagnóstico detectado)
check_planta(Planta, Diagnostico, Respuesta) :-
    Diagnostico \= healthy,
    \+ planta_tiene(Planta, Diagnostico),   % NO existe en la BD
    format(string(Respuesta), "Nuevo diagnóstico detectado: ~w en ~w. No está registrado en el sistema, se recomienda analisis adicional.", [Diagnostico, Planta]).

% Caso 4: Diagnóstico desconocido
check_planta(Planta, unknown, Respuesta) :-
    format(string(Respuesta), "No se pudo identificar el diagnostico para ~w. Se recomienda inspeccion manual.", [Planta]).

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