import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, ModelUploadForm, ModelTestForm
from .models import UserInformation, UserModel
import numpy as np
from sklearn.cluster import KMeans
from joblib import dump, load
from io import StringIO


def home(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You Have Been Logged In!")
            return redirect('home')
        else:
            messages.success(request, "There was an error!")
            return redirect('home')
    else:
        return render(request, 'home.html')

def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out!")
    return redirect('home')

def register_user(request):
    if request.user.is_authenticated:
        messages.success(request, "You Are Already Logged In!")
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            user_info = UserInformation(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone_number'],
            )

            user_info.save()

            login(request, user)

            messages.success(request, "You Have Successfully Registered!")
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'register.html', {'form': form})

def upload_model(request):
    if request.method == 'POST':
        form = ModelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user_model = UserModel()
            user_model.user = request.user
            user_model.model_name = form.cleaned_data['model_name']

            if form.cleaned_data['scores_file']:
                scores_file = form.cleaned_data['scores_file']
                scores_text = scores_file.read().decode('utf-8')
            else:
                scores_text = form.cleaned_data['scores_text']

            try:
                stripped_scores_text = ''.join(filter(lambda x: x.isdigit() or x == '\n' or x == '.', scores_text))
                scores_array = np.loadtxt(StringIO(stripped_scores_text))

                if scores_array.ndim == 1:
                    scores_array = scores_array.reshape(-1, 1)

                n_clusters = 3
                if scores_array.shape[0] < n_clusters:
                    raise ValueError(f"Not enough samples to form {n_clusters} clusters. Only {scores_array.shape[0]} samples provided.")


                kmeans = KMeans(n_clusters)
                kmeans.fit(scores_array.reshape(-1, 1))

                user_model.save()

                filename = f"user_{request.user.id}_model_{user_model.id}.joblib"
                model_file_path = os.path.join(settings.MODEL_FILE_PATH, filename)

                dump(kmeans, model_file_path)

                user_model.model_file = model_file_path
                user_model.save()
                messages.success(request, "Model uploaded successfully")
                return redirect('home')
            except ValueError as e:
                messages.error(request, f"Error processing file: {e}")
    else:
        form = ModelUploadForm()
    return render(request, 'upload_model.html', {'form': form})

def test_model(request):
    if request.method == 'POST':
        form = ModelTestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            selected_model = form.cleaned_data['model_choice']

            if form.cleaned_data['test_scores_file']:
                test_scores_file = form.cleaned_data['test_scores_file']
                test_scores_text = test_scores_file.read().decode('utf-8')
            else:
                test_scores_text = form.cleaned_data['test_scores_text']

            test_scores_array = np.loadtxt(StringIO(test_scores_text), ndmin=2)

            model_file_path = selected_model.model_file
            kmeans = load(model_file_path)

            predictions = kmeans.predict(test_scores_array.reshape(-1, 1))
            predictions = predictions.tolist()

            return render(request, 'result.html', {'predictions': predictions, 'form': form})

    else:
        form = ModelTestForm(user=request.user)
    
    return render(request, 'test_model.html', {'form': form})