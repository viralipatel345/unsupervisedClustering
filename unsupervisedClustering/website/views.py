import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, ModelUploadForm, ModelTestForm
from .models import UserInformation, UserModel
import base64
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from joblib import dump, load
from io import StringIO, BytesIO


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

def parse_scores(text):
    scores = []
    for line in text.splitlines():
        try:
            pair = [float(x) for x in line.split()]
            if len(pair) != 2:
                raise ValueError("Each line must contain exactly two numbers.")
            scores.append(pair)
        except ValueError:
            raise ValueError("Invalid format in scores data.")
    return np.array(scores)

def upload_model(request):
    if request.method == 'POST':
        form = ModelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                if form.cleaned_data['scores_file']:
                    scores_file = form.cleaned_data['scores_file']
                    if not scores_file.name.endswith('.txt'):
                        raise ValueError("Please upload a valid .txt file.")
                    scores_text = scores_file.read().decode('utf-8')
                else:
                    scores_text = form.cleaned_data['scores_text']
                scores_array = parse_scores(scores_text)

                n_clusters = 3
                if scores_array.shape[0] < n_clusters:
                    raise ValueError(f"Not enough samples to form {n_clusters} clusters.")
                kmeans = KMeans(n_clusters)
                kmeans.fit(scores_array)

                user_model = UserModel()
                user_model.user = request.user
                user_model.model_name = form.cleaned_data['model_name']
                user_model.kmeans_centers = kmeans.cluster_centers_.tolist()

                model_filename = f"user_{request.user.id}_model_{user_model.id}.joblib"
                model_file_path = os.path.join(settings.MODEL_FILE_PATH, model_filename)
                dump(kmeans, model_file_path)

                user_model.model_file = model_file_path
                user_model.save()
                messages.success(request, "Model uploaded successfully")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
                return render(request, 'upload_model.html', {'form': form})
    else:
        form = ModelUploadForm()
    return render(request, 'upload_model.html', {'form': form})

def test_model(request):
    if request.method == 'POST':
        form = ModelTestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            selected_model = form.cleaned_data['model_choice']

            try:
                if form.cleaned_data['test_scores_file']:
                    test_scores_file = form.cleaned_data['test_scores_file']
                    if not test_scores_file.name.endswith('.txt'):
                        raise ValueError("Please upload a valid .txt file.")
                    test_scores_text = test_scores_file.read().decode('utf-8')
                else:
                    test_scores_text = form.cleaned_data['test_scores_text']
                test_scores_array = parse_scores(test_scores_text)

                if test_scores_array.ndim == 1:
                    test_scores_array = test_scores_array.reshape(-1, 1)

                model_file_path = selected_model.model_file
                kmeans = load(model_file_path)
                predictions = kmeans.predict(test_scores_array)

                plt.figure(figsize=(8, 6))
                if test_scores_array.shape[1] == 1:
                    plt.scatter(test_scores_array[:, 0], np.zeros_like(test_scores_array[:, 0]), c=predictions, cmap='viridis', marker='o')
                else:
                    plt.scatter(test_scores_array[:, 0], test_scores_array[:, 1], c=predictions, cmap='viridis', marker='o')
                if selected_model.kmeans_centers:
                    centers = np.array(selected_model.kmeans_centers)
                    if centers.ndim == 1 or centers.shape[1] == 1:
                        plt.scatter(centers, np.zeros_like(centers), c='red', marker='x')
                    else:
                        plt.scatter(centers[:, 0], centers[:, 1], c='red', marker='x')

                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                plt.close()
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()

                return render(request, 'result.html', {'image_base64': image_base64})
            except Exception as e:
                messages.error(request, f"Error processing data: {e}")
                return render(request, 'test_model.html', {'form': form})
    else:
        form = ModelTestForm(user=request.user)
    
    return render(request, 'test_model.html', {'form': form})