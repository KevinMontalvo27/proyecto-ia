:- use_module(library(odbc)).
:- use_module(library(process)).
:- dynamic planta_tiene/2.

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
