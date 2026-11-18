# Propuesta de mejoras — HRM Open

**Documento para revisión del creador del proyecto**  
**Fecha: 18 noviembre 2026  
**Alcance:** cambios realizados sobre el código base de HRM Open (entorno local)

Este documento resume las funcionalidades agregadas o modificadas desde la apertura del proyecto, con el objetivo de que puedan evaluarse y aprobarse (o ajustarse) antes de incorporarlas de forma definitiva.

---

## 1. Sección Reportes

### Qué hicimos
Se agregó un módulo de **Reportes** con indicadores de RRHH y gráficos visuales.

### Qué hace
Muestra KPIs calculados a partir de legajos, ausencias y reclutamiento:
- **Total nómina** (empleados activos)
- **Rotación** (bajas del año / nómina promedio)
- **Tiempo de contratación** (días promedio hasta “contratado”)
- **Tasa de ausentismo** (días de ausencia vs. días posibles)

Y tres gráficos:
- Evolución de nómina (activos vs inactivos, últimos 12 meses)
- Distribución de nómina por área (torta)
- Postulaciones por estado del pipeline (dona)

### Cómo se usa
1. Ingresar al sistema con un usuario **Administrador** u **Operador**.
2. Ir a **Inicio → Reportes** o al menú lateral **Reportes**.
3. URL: `/reports/`
4. Los datos se actualizan solos según lo cargado en legajos, certificados y reclutamiento.

---

## 2. Navegación lateral colapsable

### Qué hicimos
Se reemplazó la navegación dispersa por un **menú lateral colapsable**, compartido en las pantallas del sistema interno.

### Qué hace
- Acceso rápido a todos los módulos permitidos según el rol.
- En escritorio se puede colapsar a íconos.
- En móvil funciona como menú drawer.
- Recuerda el estado colapsado en el navegador.
- Barra superior y menú quedan fijos; solo scrollea el contenido (se corrigió el espacio blanco al scrollear).

### Cómo se usa
1. Usar el botón **☰** de la barra superior para abrir/cerrar o colapsar.
2. En escritorio, también el botón **Colapsar** al pie del menú.
3. El ítem activo queda resaltado en azul.

---

## 3. Roles y ABM de Usuarios

### Qué hicimos
Se implementó un sistema de roles con tres perfiles y una sección para administrar usuarios.

### Roles definidos

| Rol | Permisos |
|-----|----------|
| **Administrador** | Acceso total (incluye Usuarios y Configuraciones) |
| **Operador** | Legajos, reclutamiento, certificados, reportes y recibos |
| **Colaborador** | Certificados y consulta de recibos propios |

### Qué hace
- Asigna un rol por usuario (grupos de Django).
- Restringe menús, tarjetas de inicio y vistas según permisos.
- Permite alta, edición, activación/desactivación de usuarios.
- En el legajo se puede vincular un **Usuario del sistema** (necesario para que un colaborador vea sus recibos).

### Cómo se usa
1. Entrar como **Administrador**.
2. Ir a **Usuarios** (`/users/`).
3. Crear o editar un usuario y elegir el rol.
4. Para colaboradores: en el legajo correspondiente, completar el campo **Usuario del sistema**.

**Usuarios de prueba creados en el entorno local (solo desarrollo):**
- `demo` / `demo1234` → Administrador  
- `operador` / `operador123` → Operador  
- `colaborador` / `colaborador123` → Colaborador  

---

## 4. Recibos de sueldo

### Qué hicimos
Se agregó la sección **Recibos de sueldo**, asociada a cada legajo/colaborador, con carga individual, masiva y API.

### Qué hace
- Lista recibos ordenados del más reciente al más antiguo.
- Permite **ver** (PDF) y **descargar**.
- Colaborador: solo ve los suyos (si está vinculado al legajo).
- Admin/Operador: ven todos, pueden filtrar, cargar y eliminar.

### Carga masiva (sugerencia implementada)
Para no cargar uno por uno:
1. Se elige mes y año de la liquidación.
2. Se sube un **ZIP** (o varios PDF).
3. El sistema asocia cada archivo por **DNI, CUIL o legajo** en el nombre del archivo.

Ejemplos de nombres válidos:
- `30123456.pdf`
- `20-30123456-9.pdf`
- `LEG-001.pdf`
- `recibo_30123456_noviembre.pdf`

Al finalizar muestra qué archivos se asociaron y cuáles no.

### Cómo se usa
1. Menú **Recibos** → `/payslips/`
2. Admin/Operador: botones **Carga individual** o **Cargar recibos de nómina**.
3. Colaborador: solo listado propio con Ver / Descargar.

---

## 5. Configuraciones (solo Administrador)

### Qué hicimos
Se creó un panel de **Configuraciones** con tres bloques: Correo, API de recibos y Notificaciones.

### 5.1 Correo electrónico
**Qué hace:** configura SMTP, remitente y una **plantilla HTML** para el diseño de los mails de notificación.  
**Variables de plantilla:** `company_name`, `subject`, `body`, `year`.  
**Cómo se usa:** Configuraciones → Correo → completar SMTP → Guardar → opcionalmente “Enviar correo de prueba”.

### 5.2 API de carga de recibos
**Qué hace:** permite generar **API Key + API Token** para que un ERP o sistema de liquidación cargue recibos sin usar la interfaz web. El token se muestra **una sola vez**.

**Endpoints:**
- `GET /api/v1/health/` — verificación
- `POST /api/v1/payslips/` — recibo individual (`year`, `month`, `file`, `dni`/`cuil`/`legajo`)
- `POST /api/v1/payslips/bulk/` — carga masiva (`year`, `month`, `zip_file`)

**Headers requeridos:**
```http
X-API-Key: <api_key>
X-API-Token: <api_token>
```

**Cómo se usa:** Configuraciones → API de recibos → Generar Key + Token → usar esas credenciales desde el ERP.

### 5.3 Notificaciones
**Qué hace:** define reglas por evento (activas/inactivas), asunto, cuerpo, destinatarios (Administradores, Operadores, colaborador involucrado y/o emails sueltos).

**Eventos incluidos:**
- Colaborador cargó un certificado
- Nuevo recibo de sueldo
- Nuevo CV / postulación ingresada

Las notificaciones se muestran en **acordeón colapsado** para reducir el scroll.

**Cómo se usa:** Configuraciones → Notificaciones → abrir cada evento → editar → Guardar.

---

## 6. Portal público de empleo (frontend separado)

### Qué hicimos
Se creó un **frontend público independiente** para que un candidato cargue su CV **sin acceso** al sistema HRM interno (sin menú, sin legajos, sin configuración).

### Qué hace
- Muestra búsquedas abiertas (si hay).
- Formulario de postulación (nombre, apellido, email, teléfono, búsqueda opcional, CV PDF/DOCX, consentimiento).
- Guarda el perfil en **Postulantes** con origen “Portal”.
- Si eligió una búsqueda, crea la postulación en el pipeline.
- Puede disparar la notificación de “Nuevo CV”.

### Cómo se usa
- URL pública: http://127.0.0.1:8000/empleo/
- Gracias: `/empleo/gracias/`
- Alias técnico equivalente: `/recruitment/portal/apply/`

Compartir solo `/empleo/` a candidatos. El HRM interno queda en `/` con login.

---

## 7. Ajustes de experiencia de usuario (Inicio)

### Qué hicimos
- El ítem de menú **Dashboard** pasó a llamarse **Inicio**.
- En la pantalla inicial se quitaron títulos/descripciones generales; quedan solo las funcionalidades disponibles según rol.
- Se quitaron los botones de cada tarjeta: **todo el recuadro es clickeable**.

### Cómo se usa
Al entrar al sistema (`/`), hacer clic en cualquier tarjeta visible para ir al módulo.

---

## Resumen de URLs nuevas / relevantes

| Funcionalidad | URL |
|---------------|-----|
| Inicio | `/` |
| Reportes | `/reports/` |
| Usuarios | `/users/` |
| Recibos | `/payslips/` |
| Carga masiva de recibos | `/payslips/carga-masiva/` |
| Configuraciones | `/settings/` |
| Correo | `/settings/email/` |
| API recibos | `/settings/api/` |
| Notificaciones | `/settings/notifications/` |
| Portal candidatos | `/empleo/` |
| API health | `/api/v1/health/` |
| API recibo individual | `/api/v1/payslips/` |
| API recibos masivos | `/api/v1/payslips/bulk/` |

---

## Notas técnicas para el creador

- Stack existente respetado: **Django 4.2**, Bootstrap, SQLite local (también compatible con Docker/PostgreSQL del proyecto).
- Roles basados en **grupos de Django** (`Administrador`, `Operador`, `Colaborador`).
- Recibos: modelo `Payslip` + vínculo opcional `Employee.user`.
- Configuraciones: modelos en app `core` (`EmailSettings`, `ApiCredential`, `NotificationRule`).
- API de recibos: vistas Django con autenticación por headers (sin agregar Django REST Framework).
- Portal público: templates propios en `templates/portal/` (no usa el layout del HRM).
- Archivos/migraciones principales involucrados: `accounts/`, `employees/` (reportes, recibos), `core/` (settings + API), `templates/`, `recruitment/views.py` (portal).

---

## Pedido de revisión

Se solicita al creador del proyecto revisar y indicar, por cada ítem:

1. **Aprobado**  
2. **Aprobado con cambios** (indicar ajustes)  
3. **No incorporar**

Ítems a marcar:

- [ ] Reportes (KPIs + gráficos)  
- [ ] Navegación lateral colapsable  
- [ ] Roles + ABM de usuarios  
- [ ] Recibos de sueldo (individual + masiva)  
- [ ] Configuración de correo + plantilla HTML  
- [ ] API de recibos (Key/Token + endpoints)  
- [ ] Reglas de notificaciones  
- [ ] Portal público `/empleo/`  
- [ ] Ajustes de Inicio (nombre, tarjetas clickeables)  

---

*Documento generado a partir del trabajo realizado sobre HRM Open en el entorno local.*
