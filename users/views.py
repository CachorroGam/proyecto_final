from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from .models import Profile
from django.db.models import Max
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm
from django.db.models import Count
from .models import Prestamo, Libro
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from .models import Libro
from django.shortcuts import render, get_object_or_404
from .forms import LibroForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User, Group
from .forms import UserForm  
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Libro, Prestamo
from django.utils import timezone
from users.models import Prestamo
from .forms import EditarPrestamoForm
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import logout
from django.utils.decorators import decorator_from_middleware
from django.middleware.cache import CacheMiddleware


admin_group, created = Group.objects.get_or_create(name='Administrador')
empleado_group, created = Group.objects.get_or_create(name='Empleado')  
usuario_group, created = Group.objects.get_or_create(name='Usuario')


def index(request):
    libros = Libro.objects.all() 
    return render(request, 'users/index.html', {'libros': libros})




class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to='/')
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save()

            user_group = Group.objects.get(name='Usuario')
            user.groups.add(user_group)

            last_membership = Profile.objects.aggregate(Max('numero_membresia'))['numero_membresia__max']
            if last_membership is None:
                numero_membresia = 100000 
            else:
                numero_membresia = last_membership + 1 

            print(f'Último número de membresía: {last_membership}, Nuevo número de membresía: {numero_membresia}')

            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={'numero_membresia': numero_membresia, 'role': 'Usuario', 'avatar': 'default.jpg', 'bio': ''}
            )

            if not created and profile.numero_membresia is None:
                profile.numero_membresia = numero_membresia
                profile.save()

            if created:
                messages.success(request, f'Cuenta creada para {user.username} con el número de membresía {numero_membresia}')
            else:
                messages.info(request, f'Ya existe un perfil para {user.username}. Número de membresía: {profile.numero_membresia}')

            return redirect(to='login')

        return render(request, self.template_name, {'form': form})



class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True

        user = self.request.user

        if user.groups.filter(name='Administradores').exists():
            messages.success(self.request, '¡Bienvenido Administrador!')
            return redirect('users/dash_admin') 

        elif user.groups.filter(name='Empleados').exists():
            messages.success(self.request, '¡Bienvenido Empleado!')
            return redirect('users/dash_empleado') 

        elif user.groups.filter(name='Lectores').exists():
            messages.success(self.request, '¡Bienvenido Lector!')
            return redirect('users/dash_lector') 

        messages.success(self.request, '¡Bienvenido a la plataforma!')
        return super().form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('users-home')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-home')


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect(to='users-profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {'user_form': user_form, 'profile_form': profile_form})



def dash_admin(request):
    total_libros = Libro.objects.count()
    libros_disponibles = Libro.objects.filter(disponible=True).count()
    total_prestamos = Prestamo.objects.count()
    prestamos_activos = Prestamo.objects.filter(estado='prestado').count()

    libros_mas_prestados = Prestamo.objects.values('libro__titulo') \
        .annotate(total=Count('libro')) \
        .order_by('-total')[:5]

    context = {
        'total_libros': total_libros,
        'libros_disponibles': libros_disponibles,
        'total_prestamos': total_prestamos,
        'prestamos_activos': prestamos_activos,
        'libros_mas_prestados': libros_mas_prestados
    }

    return render(request, 'users/dash_admin.html', context)






def dash_empleado(request):
    total_libros = Libro.objects.count()
    libros_disponibles = Libro.objects.filter(disponible=True).count()
    total_prestamos = Prestamo.objects.count()
    prestamos_activos = Prestamo.objects.filter(estado='prestado').count()

    libros_mas_prestados = Prestamo.objects.values('libro__titulo') \
        .annotate(total=Count('libro')) \
        .order_by('-total')[:5]

    context = {
        'total_libros': total_libros,
        'libros_disponibles': libros_disponibles,
        'total_prestamos': total_prestamos,
        'prestamos_activos': prestamos_activos,
        'libros_mas_prestados': libros_mas_prestados
    }

    return render(request, 'users/dash_empleado.html', context)




def dash_usuario(request):
    libros = Libro.objects.all() 
    return render(request, 'users/dash_usuario.html', {'libros': libros})





def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.groups.filter(name='Administrador').exists():
                return redirect('dash_admin')
            elif user.groups.filter(name='Empleado').exists(): 
                return redirect('dash_empleado')
            elif user.groups.filter(name='Usuario').exists():
                return redirect('dash_usuario')
            else:
                return render(request, 'sin_permiso.html', {'mensaje': 'No tiene rol asignado'})
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})







def profile_admin(request):
    user = request.user
    return render(request, 'users/profile_admin.html', {'user': user})



@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    response = render(request, 'users/profile.html', {'user_profile': user_profile})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def profile_empleado_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    response = render(request, 'users/profile_empleado.html', {'user_profile': user_profile})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def profile_users_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    response = render(request, 'users/profile_users.html', {'user_profile': user_profile})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def settings_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        notifications = request.POST.get('notifications') == 'on'
        profile_picture = request.FILES.get('profile_picture') 

        request.user.username = username
        request.user.email = email
        request.user.notifications = notifications 
        request.user.save()

        if new_password and new_password == confirm_password:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, '¡La contraseña se ha actualizado correctamente!')
        elif new_password:
            messages.error(request, 'Las contraseñas no coinciden.')

        # Manejo de la foto de perfil
        if profile_picture:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            user_profile.profile_picture = profile_picture 
            user_profile.save()
            messages.success(request, '¡La foto de perfil se ha actualizado correctamente!')

        messages.success(request, '¡La configuración se ha actualizado correctamente!')
        return redirect('settings')

    return render(request, 'users/settings.html')


@login_required
def settings_empleado_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        notifications = request.POST.get('notifications') == 'on'
        profile_picture = request.FILES.get('profile_picture')  


        request.user.username = username
        request.user.email = email
        request.user.notifications = notifications
        request.user.save()

        if new_password and new_password == confirm_password:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, '¡La contraseña se ha actualizado correctamente!')
        elif new_password:
            messages.error(request, 'Las contraseñas no coinciden.')

        if profile_picture:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            user_profile.profile_picture = profile_picture 
            user_profile.save()
            messages.success(request, '¡La foto de perfil se ha actualizado correctamente!')

        messages.success(request, '¡La configuración se ha actualizado correctamente!')
        return redirect('settings_empleado')

    return render(request, 'users/settings_empleado.html')




@login_required
def settings_usuario_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        notifications = request.POST.get('notifications') == 'on'
        profile_picture = request.FILES.get('profile_picture') 

        if User.objects.filter(username=username).exclude(id=request.user.id).exists():
            messages.error(request, 'Este nombre de usuario ya está siendo utilizado.')
            return redirect('settings_usuario') 


        request.user.username = username
        request.user.email = email
        request.user.notifications = notifications 
        request.user.save()


        if new_password and new_password == confirm_password:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, '¡La contraseña se ha actualizado correctamente!')
        elif new_password:
            messages.error(request, 'Las contraseñas no coinciden.')

        if profile_picture:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            user_profile.profile_picture = profile_picture 
            user_profile.save()
            messages.success(request, '¡La foto de perfil se ha actualizado correctamente!')

        messages.success(request, '¡La configuración se ha actualizado correctamente!')
        return redirect('settings_usuario')

    return render(request, 'users/settings_usuario.html')




@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, 'Tu cuenta ha sido eliminada con éxito.')
        return redirect('index') 
    return redirect('settings')  





@login_required
def listar_libros(request):
    libros = Libro.objects.all() 

    response = render(request, 'users/libros_list.html', {'libros': libros})

    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

@login_required
def listar_libros_empleado(request):
    libros = Libro.objects.all() 

    response = render(request, 'users/libros_list_empleado.html', {'libros': libros})

    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

@login_required
def listar_libros_users(request):
    libros = Libro.objects.all() 

    response = render(request, 'users/listar_libros_users.html', {'libros': libros})

    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


def listar_libro(request):
    libros = Libro.objects.all() 

    return render(request, 'users/listar_libro.html', {'libros': libros})

    # # Deshabilitar el almacenamiento en caché
    # response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    # response['Pragma'] = 'no-cache'
    # response['Expires'] = '0'

    # return response


def detalles_libro(request, id):
    libro = get_object_or_404(Libro, id=id)
    
    return render(request, 'users/detalles_libro.html', {'libro': libro})

def detalles_libro_pre(request, id):
    libro = get_object_or_404(Libro, id=id)
    
    return render(request, 'users/detalles_libro_pre.html', {'libro': libro})



def mis_prestamos(request):
    prestamos = Prestamo.objects.filter(usuario=request.user).select_related('libro')
    return render(request, 'users/mis_prestamos.html', {'prestamos': prestamos})




@login_required
def registrar_libro(request):
    if request.method == 'POST':
        form = LibroForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            return redirect('libros')
    else:
        form = LibroForm()
    
    return render(request, 'users/register_libro.html', {'form': form})

@login_required
def registrar_libro_empleado(request):
    if request.method == 'POST':
        form = LibroForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('libros_empleado') 
    else:
        form = LibroForm()
    
    return render(request, 'users/register_libro_empleado.html', {'form': form})




def editar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)

    if request.method == 'POST':
        form = LibroForm(request.POST, request.FILES, instance=libro)
        if form.is_valid():
            form.save()
            return redirect('dash_admin') 
    else:
        form = LibroForm(instance=libro)

    return render(request, 'users/editar_libro.html', {'form': form, 'libro': libro})



def eliminar_libro(request, id):
    libro = get_object_or_404(Libro, id=id)

    if request.method == 'POST':
        libro.delete()
        return redirect('dash_admin')

    return redirect('dash_admin')  



def users(request):
    all_users = User.objects.all()  
    return render(request, 'users/users.html', {'all_users': all_users})


def users_empleado(request):
    all_users = User.objects.all() 
    return render(request, 'users/users_empleado.html', {'all_users': all_users})





def eliminar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('users')  


def editar_usuario(request, id):
    user = get_object_or_404(User, id=id)
    
    tiene_administrador = user.groups.filter(name="Administrador").exists()
    tiene_empleado = user.groups.filter(name="Empleado").exists()
    tiene_usuario = user.groups.filter(name="Usuario").exists()
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        
        password_form = PasswordChangeForm(user, request.POST)
        
        new_role = request.POST.get('role')  
        
        if password_form.is_valid():
            user.set_password(password_form.cleaned_data['new_password1'])
            user.save()
            messages.success(request, "Contraseña cambiada con éxito")
        
        if new_role:
            group = Group.objects.get(name=new_role)
            user.groups.clear() 
            user.groups.add(group)  
            
            messages.success(request, f"Rol cambiado a {new_role}")

        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente")
            return redirect('users')  
    else:
        form = UserForm(instance=user)
        password_form = PasswordChangeForm(user)
    
    return render(request, 'users/editar_usuario.html', {
        'form': form,
        'password_form': password_form,
        'user': user,
        'tiene_administrador': tiene_administrador,
        'tiene_empleado': tiene_empleado,
        'tiene_usuario': tiene_usuario,
    })



def editar_usuario_empleado(request, id):
    user = get_object_or_404(User, id=id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        
        password_form = PasswordChangeForm(user, request.POST)
        
        if password_form.is_valid():
            user.set_password(password_form.cleaned_data['new_password1'])
            user.save()
            messages.success(request, "Contraseña cambiada con éxito")
        
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente")
            return redirect('users')
    
    else:
        form = UserForm(instance=user)
        password_form = PasswordChangeForm(user)
    
    return render(request, 'users/editar_usuario_empleado.html', {
        'form': form,
        'password_form': password_form,
        'user': user,
    })



def contacto(request):
    return render(request, 'users/contacto.html')



@login_required
def contacto_users(request):

    context = {}
    response = render(request, 'users/contacto_users.html', context)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response




def reservar_libro(request, libro_id):
    libro = Libro.objects.get(id=libro_id)
    
    if libro.reservado:
        if libro.reservado_por == request.user:
            libro.reservado = False
            libro.reservado_por = None
            libro.save()
            messages.success(request, f'Has cancelado tu reserva del libro: {libro.titulo}')
        else:
            messages.error(request, f'Este libro ya está reservado por otro usuario.')
    else:
        libro.reservado = True
        libro.reservado_por = request.user
        libro.save()
        messages.success(request, f'Has reservado el libro: {libro.titulo}')

    return redirect('detalles_libro', id=libro.id)



@login_required
def cancelar_reserva(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id, reservado_por=request.user)

    libro.reservado = False
    libro.reservado_por = None
    libro.save()
    messages.success(request, f'Has cancelado la reserva del libro "{libro.titulo}".')

    return redirect('detalles_libro', id=libro_id)




def reservas_view(request):
    reservas = Libro.objects.filter(reservado=True) 
    context = {
        'reservas': reservas
    }
    return render(request, 'users/reservas.html', context)



def reservas_empleado_view(request):
    reservas = Libro.objects.filter(reservado=True)  
    context = {
        'reservas': reservas
    }
    return render(request, 'users/reservas_empleado.html', context)


def eliminar_reserva(request, id):
    libro = get_object_or_404(Libro, id=id)

    if libro.reservado:
        libro.reservado = False 
        libro.reservado_por = None  
        libro.save()  

        messages.success(request, f'La reserva del libro "{libro.titulo}" ha sido eliminada exitosamente.')
    else:
        messages.error(request, 'Este libro no tiene una reserva activa.')

    return redirect('reservas')



def registrar_prestamo(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    
    if libro.disponible:
        prestamo = Prestamo.objects.create(
            libro=libro,
            usuario=request.user,
            fecha_prestamo=timezone.now()
        )

        libro.disponible = False
        libro.save()

        messages.success(request, f'El libro "{libro.titulo}" ha sido prestado exitosamente.')
    else:
        messages.error(request, f'El libro "{libro.titulo}" no está disponible para préstamo.')

    return redirect('reservas')




def editar_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)
    
    if request.method == 'POST':
        form = EditarPrestamoForm(request.POST, instance=prestamo)
        if form.is_valid():
            fecha_prestamo = form.cleaned_data['fecha_prestamo']
            fecha_devolucion = form.cleaned_data['fecha_devolucion']

            if fecha_devolucion and fecha_prestamo:
                dias_prestamo = (fecha_devolucion - fecha_prestamo).days
                prestamo.dias_prestamo = dias_prestamo
                prestamo.save()

            form.save()
            messages.success(request, 'El préstamo se ha actualizado correctamente.')
            return redirect('reservas') 
    else:
        form = EditarPrestamoForm(instance=prestamo)
    
    return render(request, 'users/editar_prestamo.html', {'form': form, 'prestamo': prestamo})





def devolver_libro_view(request, reserva_id):
    reserva = get_object_or_404(Prestamo, id=reserva_id)

    if reserva.usuario != request.user:
        messages.error(request, 'Esta reserva no pertenece a su cuenta.')
        return redirect('reservas_lista') 

    if request.method == 'POST':
        confirmacion = request.POST.get('confirmar_devolucion')
        
        if confirmacion == 'si':
            if reserva.estado != 'devuelto': 
                reserva.estado = 'devuelto'
                reserva.fecha_devolucion = timezone.now()  
                reserva.libro.disponible = True 
                reserva.libro.save()  
                reserva.save()  

                messages.success(request, '¡Libro devuelto con éxito!')
            else:
                messages.warning(request, 'Este libro ya ha sido devuelto anteriormente.')

            return redirect('reservas')  
        else:
            messages.info(request, 'La devolución ha sido cancelada.')

    return render(request, 'users/devolucion_prestamo.html', {'reserva': reserva})






def devolucion_prestamo_view(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)

    if request.method == 'POST':
        prestamo.estado = 'Devuelto'
        prestamo.save()
        return redirect('prestamos_activos')  

    return render(request, 'users/devolucion_prestamo.html', {'prestamo': prestamo})





def prestamos_activos_view(request):
    prestamos = Prestamo.objects.all()  
    return render(request, 'users/prestamos_activos.html', {'prestamos': prestamos})



def prestamos_activos_empleado_view(request):
    prestamos = Prestamo.objects.all()   
    return render(request, 'users/prestamos_activos_empleado.html', {'prestamos': prestamos})




def historial_prestamos(request):
    prestamos = Prestamo.objects.all().order_by('-fecha_prestamo') 
    return render(request, 'users/historial_prestamos.html', {'prestamos': prestamos})


def historial_prestamos_empleado(request):

    prestamos = Prestamo.objects.all().order_by('-fecha_prestamo') 
    return render(request, 'users/historial_prestamos_empleado.html', {'prestamos': prestamos})





def logout_view(request):
    logout(request) 
    return redirect('login')  





def no_cache(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return _wrapped_view_func



