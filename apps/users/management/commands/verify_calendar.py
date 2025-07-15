from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, date
from apps.users.models import User, CalendarEvent
from apps.users.views import get_user_events, prepare_calendar_data, get_calendar_stats

class Command(BaseCommand):
    help = 'Verifica que los eventos del calendario se muestren correctamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID del usuario para verificar eventos',
        )
        parser.add_argument(
            '--month',
            type=int,
            default=timezone.now().month,
            help='Mes a verificar (1-12)',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Año a verificar',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        month = options['month']
        year = options['year']
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Usuario con ID {user_id} no encontrado'))
                return
        else:
            user = User.objects.filter(is_active=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('No se encontraron usuarios'))
                return

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🔍 VERIFICACIÓN DEL CALENDARIO'))
        self.stdout.write('='*60)
        self.stdout.write(f'👤 Usuario: {user.get_full_name()} (ID: {user.id}, Tipo: {user.get_user_type_display()})')
        self.stdout.write(f'📅 Período: {month:02d}/{year}')

        # Calcular rango de fechas del mes
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)

        self.stdout.write(f'📆 Rango: {first_day} - {last_day}')

        # 1. Verificar eventos directos en la base de datos
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('📊 EVENTOS EN BASE DE DATOS')
        self.stdout.write('-'*40)
        
        all_events = CalendarEvent.objects.filter(
            start_date__date__gte=first_day,
            start_date__date__lte=last_day
        )
        
        user_events_direct = CalendarEvent.objects.filter(
            start_date__date__gte=first_day,
            start_date__date__lte=last_day,
            user=user
        )
        
        self.stdout.write(f'🔢 Total eventos en BD (período): {all_events.count()}')
        self.stdout.write(f'👤 Eventos directos del usuario: {user_events_direct.count()}')
        
        if user_events_direct.exists():
            for event in user_events_direct:
                self.stdout.write(f'  📅 {event.start_date.strftime("%d/%m")} - {event.title} ({event.event_type})')

        # 2. Verificar función get_user_events
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('🔄 FUNCIÓN get_user_events')
        self.stdout.write('-'*40)
        
        try:
            events_from_function = get_user_events(user, first_day, last_day)
            self.stdout.write(f'✅ Función ejecutada exitosamente')
            self.stdout.write(f'🔢 Eventos retornados: {events_from_function.count()}')
            
            if events_from_function.exists():
                for event in events_from_function:
                    icon = event.get_icon() if hasattr(event, 'get_icon') else '❓'
                    color_class = event.get_color_class() if hasattr(event, 'get_color_class') else 'default'
                    self.stdout.write(f'  📅 {event.start_date.strftime("%d/%m %H:%M")} - {event.title}')
                    self.stdout.write(f'      🏷️  Tipo: {event.event_type} | 🎨 Clase: {color_class} | 🎯 Icono: {icon}')
                    if event.course:
                        self.stdout.write(f'      📚 Curso: {event.course.name}')
            else:
                self.stdout.write('⚠️  No se encontraron eventos')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error en get_user_events: {str(e)}'))

        # 3. Verificar estructura de datos del calendario
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('🗓️  ESTRUCTURA DEL CALENDARIO')
        self.stdout.write('-'*40)
        
        try:
            calendar_data = prepare_calendar_data(year, month, 'month')
            self.stdout.write(f'✅ Datos del calendario generados')
            self.stdout.write(f'📅 Mes: {calendar_data.get("month_name", "N/A")}')
            self.stdout.write(f'🔢 Días del mes: {len(calendar_data.get("month_days", []))} semanas')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error en prepare_calendar_data: {str(e)}'))

        # 4. Verificar eventos por fecha (events_by_date)
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('📋 EVENTOS ORGANIZADOS POR FECHA')
        self.stdout.write('-'*40)
        
        try:
            events = get_user_events(user, first_day, last_day)
            events_by_date = {}
            
            for event in events:
                date_str = event.start_date.date().strftime('%Y-%m-%d')
                if date_str not in events_by_date:
                    events_by_date[date_str] = []
                events_by_date[date_str].append(event)
            
            self.stdout.write(f'📊 Fechas con eventos: {len(events_by_date)}')
            
            for date_str, date_events in events_by_date.items():
                self.stdout.write(f'  📅 {date_str}: {len(date_events)} evento(s)')
                for event in date_events:
                    self.stdout.write(f'    - {event.title} ({event.event_type})')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error organizando eventos por fecha: {str(e)}'))

        # 5. Verificar estadísticas
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('📈 ESTADÍSTICAS DEL CALENDARIO')
        self.stdout.write('-'*40)
        
        try:
            events = get_user_events(user, first_day, last_day)
            stats = get_calendar_stats(user, events)
            
            self.stdout.write(f'📊 Estadísticas calculadas:')
            self.stdout.write(f'  🔢 Total eventos: {stats.get("total_events", 0)}')
            self.stdout.write(f'  📅 Eventos hoy: {stats.get("today_events", 0)}')
            self.stdout.write(f'  ⏭️  Eventos próximos: {stats.get("upcoming_events", 0)}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error calculando estadísticas: {str(e)}'))

        # 6. Recomendaciones
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('💡 RECOMENDACIONES')
        self.stdout.write('-'*40)
        
        if events_from_function.count() == 0:
            self.stdout.write('🔧 SUGERENCIAS:')
            self.stdout.write('  1. Ejecuta: python manage.py create_test_events --user-id ' + str(user.id))
            self.stdout.write('  2. Verifica que el usuario tenga cursos asignados')
            self.stdout.write('  3. Revisa que haya tareas creadas en el sistema')
        else:
            self.stdout.write('✅ El calendario parece funcionar correctamente')
            self.stdout.write('🌐 Accede al calendario web para verificar la visualización')

        # 7. URLs de verificación
        self.stdout.write('\n' + '-'*40)
        self.stdout.write('🌐 URLS PARA VERIFICACIÓN MANUAL')
        self.stdout.write('-'*40)
        self.stdout.write('🔗 URLs sugeridas para probar en el navegador:')
        self.stdout.write(f'  📅 Calendario: /usuarios/calendario/')
        self.stdout.write(f'  🏠 Dashboard: /usuarios/dashboard/{user.user_type}/{user.id}/')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ VERIFICACIÓN COMPLETADA'))
        self.stdout.write('='*60)
