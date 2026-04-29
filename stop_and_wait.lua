print("!!! CARGANDO MI PROTOCOLO !!!")

-- 1. Definición del protocolo
local mi_proto = Proto("SAW", "stop_and_wait")

-- 2. Definición de campos (Filtros de búsqueda)
local f = mi_proto.fields
f.protocol   = ProtoField.string("miprotocolo.protocol", "Protocolo")
f.operation  = ProtoField.string("miprotocolo.operation", "Operación")
f.file_name  = ProtoField.string("miprotocolo.file", "Nombre de Archivo")
f.seq        = ProtoField.string("miprotocolo.seq", "Secuencia")
f.end_client = ProtoField.string("miprotocolo.end_client", "End Flag")
f.data       = ProtoField.string("miprotocolo.data", "Datos (Payload)")

-- 3. Función Dissector
function mi_proto.dissector(buf, pkt, tree)
    -- Seteamos el protocolo en la lista de paquetes
    pkt.cols.protocol = "SAW"

    -- Convertimos el buffer a string para procesarlo
    local str_data = buf():string()
    local fields = {}
    local last_pos = 1
    
    -- Buscamos las posiciones de los pipes '|'
    -- Nuestro formato tiene 5 campos fijos antes de la data: 
    -- protocol|operation|file_name|seq|end_client|verbose|
    for i = 1, 5 do
        local pipe_pos = str_data:find("|", last_pos)
        if pipe_pos then
            table.insert(fields, {
                val = str_data:sub(last_pos, pipe_pos - 1),
                start = last_pos - 1,
                len = pipe_pos - last_pos
            })
            last_pos = pipe_pos + 1
        end
    end

    -- Creamos el árbol principal
    local subtree = tree:add(mi_proto, buf(0), "Mi Protocolo (Mensaje Basado en Texto)")

    -- Añadimos los campos al árbol si se encontraron
    if fields[1] then subtree:add(f.protocol,   buf(fields[1].start, fields[1].len)) end
    if fields[2] then subtree:add(f.operation,  buf(fields[2].start, fields[2].len)) end
    if fields[3] then subtree:add(f.file_name,  buf(fields[3].start, fields[3].len)) end
    if fields[4] then subtree:add(f.seq,        buf(fields[4].start, fields[4].len)) end
    if fields[5] then subtree:add(f.end_client, buf(fields[5].start, fields[5].len)) end

    -- LÓGICA DE CLASIFICACIÓN (ACK vs DATA)
    if #fields > 0 then
        -- Si hay pipes, procesamos la DATA como antes
        if last_pos <= buf:len() then
            subtree:add(f.data, buf(last_pos - 1))
        end
    else
        -- Si NO hay pipes (#fields es 0), lo marcamos como ACK
        subtree:add(f.data, buf(0)):append_text(" (Mensaje de ACK / Control)")
        pkt.cols.info = "ACK Recibido: " .. str_data
    end

    -- Información rápida en la columna INFO
    if #fields >= 3 then
        pkt.cols.info = "[" .. fields[2].val .. "] Archivo: " .. fields[3].val .. " (Seq: " .. (fields[4].val or "0") .. ")"
    end
end

function mi_proto_heuristic(buf, pkt, tree)
    -- Verificamos si el buffer tiene al menos 3 caracteres (evita errores en paquetes vacíos)
    if buf:len() < 3 then return false end

    -- Extraemos los primeros caracteres para ver si es "SAW"
    local signature = "stop_and_wait"
    local sig_len = #signature

    if buf:len() < sig_len then return false end

    -- Extraemos el inicio del paquete
    local prefix = buf(0, sig_len):string()

    if prefix == signature then
        -- Si coincide, llamamos al dissector y avisamos a Wireshark (true)
        mi_proto.dissector(buf, pkt, tree)
        return true
    end

    -- Si no empieza con "SAW", devolvemos false para que otro script intente leerlo
    return false
end

-- 4. Registro del puerto (Cámbialo por el puerto que uses en tu script de Python)
--local udp_table = DissectorTable.get("udp.port")
--udp_table:add(8080, mi_proto)
--print("!!! CARGANDO MI PROTOCOLO !!!")

mi_proto:register_heuristic("udp", mi_proto_heuristic)
