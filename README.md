# Servicio de Gráficos Tronix (Streamlit + Plotly)

Micro‑servicio que renderiza gráficos interactivos a partir de datos guardados en Supabase.  
Diseñado para ser desplegado en **Railway** y consumido por tu agente Tronix vía URL (iframe).

## 🚀 Despliegue rápido

1. **Clona el repo**  
   ```bash
   git clone https://github.com/tuusuario/graficos-service.git
   cd graficos-service
   ```

2. **Variables de entorno (Railway → _Variables_)**

   | Variable | Valor (ejemplo) |
   |----------|-----------------|
   | `SUPABASE_URL` | https://kvenozirujsvjrsmpqhu.supabase.co |
   | `SUPABASE_SERVICE_ROLE` | _tu key service_role_ |

3. **Deploy en Railway**  
   Railway detectará el `requirements.txt` y el `Procfile`.
   El servidor quedará expuesto en `https://<subdominio>.up.railway.app`.

## 📝 Uso

```
https://<tu-app>.up.railway.app/?grafico_id=<uuid>
```

El agente Tronix incluye esta URL en su respuesta y el frontend la incrusta en un iframe.

## 🗄️ Estructura

```
.
├─ streamlit_app.py      # app principal
├─ supabase_client.py    # helper Supabase
├─ requirements.txt
└─ Procfile
```

## 📄 Licencia

MIT
