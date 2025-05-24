

from datetime import datetime
from django.shortcuts import render
from .models import Flight, Tour, Hotel  # Điều chỉnh tùy theo app bạn
from collections import defaultdict

def ai_recommend(request):
    itinerary = None

    city_to_airport_code = {
        'Đà Nẵng': 'Đà Nẵng',
        'Đà Lạt': 'Đà Lạt',
        'Phú Quốc': 'Phú Quốc',
        'Hạ Long': 'Hạ Long',
        'Nha Trang': 'CXR',
    }

    start_city_default = 'Đà Nẵng'
    destination_default = 'Phú Quốc'
    default_budget = 5
    default_people = 1

    

    def parse_int(value, default):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    selected_start_city = start_city_default
    selected_destination_city = destination_default
    selected_day = ''
    selected_month = ''
    selected_year = ''
    selected_start_day_str = ''

    start_code = city_to_airport_code.get(start_city_default)
    dest_code = city_to_airport_code.get(destination_default)

    available_start_days = Flight.objects.filter(
        take_place=start_code,
        destination=dest_code,
    ).values_list('Start_Day', flat=True).distinct()
    print(start_code, dest_code)  # kiểm tra mã sân bay
    print(list(available_start_days))  # xem có dữ liệu không

    def split_date_parts(date_str):
        try:
            day, month, year = date_str.split('-')
            return int(day), int(month), int(year)
        except:
            return None, None, None

    available_dates = [split_date_parts(d) for d in available_start_days if d]
    available_days = sorted(set(d for d, m, y in available_dates if d))
    available_months = sorted(set(m for d, m, y in available_dates if m))
    available_years = sorted(set(y for d, m, y in available_dates if y))

    if request.method == 'POST':
        budget_million = parse_int(request.POST.get('budget'), default_budget)
        people = parse_int(request.POST.get('people'), default_people)
        selected_start_city = request.POST.get('start_city', start_city_default)
        selected_destination_city = request.POST.get('destination_city', destination_default)
        selected_day = request.POST.get('start_day', '')
        selected_month = request.POST.get('start_month', '')
        selected_year = request.POST.get('start_year', '')

        budget = budget_million * 1_000_000
        start_code = city_to_airport_code.get(selected_start_city, selected_start_city)
        dest_code = city_to_airport_code.get(selected_destination_city, selected_destination_city)

        all_flights = Flight.objects.filter(take_place=start_code, destination=dest_code)

        available_start_days = all_flights.values_list('Start_Day', flat=True).distinct()
        available_dates = [split_date_parts(d) for d in available_start_days if d]
        available_days = sorted(set(d for d, m, y in available_dates if d))
        available_months = sorted(set(m for d, m, y in available_dates if m))
        available_years = sorted(set(y for d, m, y in available_dates if y))

        # Tạo chuỗi ngày dd-mm-yyyy từ form
        if selected_day and selected_month and selected_year:
            try:
                selected_date_obj = datetime.strptime(
                    f"{selected_day}-{selected_month}-{selected_year}", '%d-%m-%Y'
                )
                selected_start_day_str = selected_date_obj.strftime('%d-%m-%Y')
            except ValueError:
                selected_start_day_str = ''

        if selected_start_day_str:
            selected_flights = all_flights.filter(Start_Day=selected_start_day_str)
        else:
            selected_flights = all_flights

        selected_flight = selected_flights.order_by('Price').first()

        all_tours = Tour.objects.filter(City__iexact=selected_destination_city)
        all_hotels = Hotel.objects.all()

        def normalize_city(city_name):
            return city_name.replace('Thành Phố ', '').strip().lower()

        selected_hotels = [h for h in all_hotels if normalize_city(h.hotel_city) == selected_destination_city.lower()]

        top_tours = sorted(all_tours, key=lambda t: t.rating, reverse=True)[:5]
        tour_infos = []
        hotel_infos = []

        if not selected_hotels:
            itinerary = {'error': 'Không tìm thấy khách sạn phù hợp với địa điểm đã chọn.'}
        else:
            flight_cost = (selected_flight.Price * people) if selected_flight else 0
            remaining_budget = budget - flight_cost

            if top_tours:
                for tour in top_tours:
                    tour_cost = tour.price * people
                    budget_after_tour = remaining_budget - tour_cost
                    hotel_list = []

                    for hotel in selected_hotels:
                        max_days = int(budget_after_tour / (hotel.price * people)) if hotel.price > 0 else 0
                        hotel_list.append((hotel, max_days))

                    # Bước 1: Chọn khách sạn tốt nhất mỗi phân khúc sao
                    best_hotels_by_star = {}

                    for hotel, max_days in hotel_list:
                        try:
                            if hotel.star_number is None or hotel.score_hotels is None:
                                continue
                            star = int(hotel.star_number)
                            score = float(hotel.score_hotels)
                        except (ValueError, TypeError):
                            continue

                        if star not in best_hotels_by_star or score > float(best_hotels_by_star[star][0].score_hotels):
                            best_hotels_by_star[star] = (hotel, max_days)

                    # Bước 2: Lấy danh sách khách sạn đã chọn theo phân khúc sao
                    top_hotels = list(best_hotels_by_star.values())

                    # Bước 3: Nếu chưa đủ 5 khách sạn, thêm những khách sạn còn lại theo tiêu chí phụ
                    if len(top_hotels) < 5:
                        selected_set = set(h[0].hotel_name for h in top_hotels)  # tên để tránh trùng lặp
                        remaining_hotels = [
                            (hotel, max_days)
                            for hotel, max_days in hotel_list
                            if hotel.hotel_name not in selected_set
                        ]

                        # Sắp xếp theo: điểm số giảm dần, số lượt đánh giá giảm dần, giá tăng dần
                        remaining_hotels_sorted = sorted(
                            remaining_hotels,
                            key=lambda x: (
                                -float(x[0].score_hotels or 0),
                                -int(x[0].number_rating or 0),
                                float(x[0].price or 0)
                            )
                        )

                        # Bổ sung để đủ 5 khách sạn
                        for hotel in remaining_hotels_sorted:
                            if len(top_hotels) >= 5:
                                break
                            top_hotels.append(hotel)



                    hotel_pack = [{
                        'hotel_name': h.hotel_name,
                        'location': h.location,
                        'price': h.price,
                        'score_hotels': h.score_hotels,
                        'number_rating': h.number_rating,
                        'start_clean': h.start_clean,
                        'received_time': h.received_time,
                        'giveback_time': h.giveback_time,
                        'from_center': h.from_center,
                        'popular_destination': h.popular_destination,
                        'hotel_link': h.hotel_link,
                        'max_days': max_days,
                    } for h, max_days in top_hotels]


                    tour_infos.append({
                        'tour': {
                            'tour_name': tour.tour_name,
                            'price': tour.price,
                            'rating': tour.rating,
                        },
                        'hotels': hotel_pack
                    })
            else:
                hotel_list = []
                for hotel in selected_hotels:
                    max_days = int(remaining_budget / (hotel.price * people)) if hotel.price > 0 else 0
                    hotel_list.append((hotel, max_days))

                top_hotels = sorted(hotel_list, key=lambda x: x[1], reverse=True)[:5]
                for hotel, max_days in top_hotels:
                    hotel_infos.append({
                        'hotel_name': hotel.hotel_name,
                        'location': hotel.location,
                        'price': hotel.price,
                        'score_hotels': hotel.score_hotels,
                        'number_rating': hotel.number_rating,
                        'start_clean': hotel.start_clean,
                        'received_time': hotel.received_time,
                        'giveback_time': hotel.giveback_time,
                        'from_center': hotel.from_center,
                        'popular_destination': hotel.popular_destination,
                        'hotel_link': hotel.hotel_link,
                        'max_days': max_days,
                    })

            flight_info = None
            if selected_flight:
                flight_info = {
                    'Airline': selected_flight.Airline,
                    'Price': selected_flight.Price * people,
                    'Start_Day': selected_flight.Start_Day,
                    'Start_time': selected_flight.Start_time,
                    'take_place': selected_flight.take_place,
                    'End_time': selected_flight.End_time,
                    'destination': selected_flight.destination,
                    'flight_time': selected_flight.flight_time,
                    'transit': selected_flight.transit,
                    'total_time_hour': selected_flight.total_time_hour,
                    'End_day': selected_flight.End_day,
                }

            itinerary = {
                'flight': flight_info,
                'tours': tour_infos if tour_infos else None,
                'hotels': hotel_infos if not tour_infos else None,
                'people': people,
                'budget': budget,
            }

    context = {
        'itinerary': itinerary,
        'start_city_default': start_city_default,
        'destination_default': destination_default,
        'default_budget': default_budget,
        'default_people': default_people,
        'selected_start_city': selected_start_city,
        'selected_destination_city': selected_destination_city,
        'available_days': available_days,
        'available_months': available_months,
        'available_years': available_years,
        'selected_day': selected_day,
        'selected_month': selected_month,
        'selected_year': selected_year,
    }

    return render(request, 'ai_recommend.html', context)


def homepage(request):
    return render(request, 'homepage.html')


def dashboard(request):
    return render(request, 'dashboard.html')


from django.shortcuts import render
from .models import Hotel, Flight, Tour
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
import pandas as pd
import numpy as np


AIRPORT_CODE_MAPPING = {
    'DAD': 'Đà Nẵng',
    'DLI': 'Đà Lạt',
    'VDO': 'Hạ Long',
    'PQC': 'Phú Quốc',
}

CITY_NAME_CORRECTIONS = {
    'Thành Phố Hạ Long': 'Hạ Long'
}

def normalize_flight_queryset(flights):
    df = pd.DataFrame(list(flights.values(
        'id', 'Airline', 'Price', 'Start_Day', 'Start_time', 'take_place', 
        'End_time', 'destination', 'flight_time', 'transit', 'total_time_hour', 'End_day'
    )))
    df['take_place'] = df['take_place'].map(AIRPORT_CODE_MAPPING).fillna(df['take_place'])
    df['destination'] = df['destination'].map(AIRPORT_CODE_MAPPING).fillna(df['destination'])
    df['transit'] = df['transit'].astype(str)
    
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df['flight_time'] = pd.to_numeric(df['flight_time'], errors='coerce')
    df['total_time_hour'] = pd.to_numeric(df['total_time_hour'], errors='coerce')
    
    df.dropna(subset=['Price', 'flight_time', 'total_time_hour'], inplace=True)
    df['id'] = df['id'].astype(int)
    
    return df

def normalize_hotel_queryset(hotels):
    df = pd.DataFrame(list(hotels.values(
        'hotel_id', 'hotel_city', 'star_number', 'popular_destination', 
        'price', 'score_hotels', 'number_rating'
    )))
    df['hotel_city'] = df['hotel_city'].map(CITY_NAME_CORRECTIONS).fillna(df['hotel_city'])

    numeric_cols = ['star_number', 'price', 'score_hotels', 'number_rating']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)

    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    return df

def normalize_tour_queryset(tours):
    df = pd.DataFrame(list(tours.values(
        'tour_id', 'City', 'price', 'duration', 'rating'
    )))
    numeric_cols = ['price', 'duration', 'rating']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=numeric_cols, inplace=True)

    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    return df

def build_similarity_matrix(df, id_field, categorical_features=[], numeric_features=[]):
    if df.empty:
        return pd.DataFrame()
    
    features_encoded = []
    if categorical_features:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        cat_encoded = encoder.fit_transform(df[categorical_features])
        features_encoded.append(cat_encoded)
    if numeric_features:
        num_features = df[numeric_features].values
        features_encoded.append(num_features)

    if len(features_encoded) == 2:
        combined_features = np.hstack(features_encoded)
    elif len(features_encoded) == 1:
        combined_features = features_encoded[0]
    else:
        return pd.DataFrame()
    
    sim_matrix = cosine_similarity(combined_features)
    return pd.DataFrame(sim_matrix, index=df[id_field], columns=df[id_field])

def recommend_items(user_selected_ids, similarity_matrix, top_n=5):
    if similarity_matrix.empty or not user_selected_ids:
        return []
    
    user_ids_in_matrix = [i for i in user_selected_ids if i in similarity_matrix.index]
    if not user_ids_in_matrix:
        return []

    sim_scores = similarity_matrix.loc[user_ids_in_matrix].mean(axis=0)
    sim_scores = sim_scores.drop(user_ids_in_matrix, errors='ignore')
    
    return sim_scores.sort_values(ascending=False).head(top_n).index.tolist()

def travel_recommend(request):
    all_flights = Flight.objects.all()
    all_hotels = Hotel.objects.all()
    all_tours = Tour.objects.all()

    flight_df = normalize_flight_queryset(all_flights)
    hotel_df = normalize_hotel_queryset(all_hotels)
    tour_df = normalize_tour_queryset(all_tours)

    cities = set(hotel_df['hotel_city']) | set(tour_df['City']) | set(flight_df['destination'])
    context = {'cities': sorted(cities)}

    if request.method == 'POST':
        selected_city = request.POST.get('city')
        
        # Fix: Add validation for people input
        try:
            people = int(request.POST.get('people', 1))
            if people <= 0:
                people = 1
        except (ValueError, TypeError):
            people = 1

        hotels_filtered = hotel_df[hotel_df['hotel_city'] == selected_city]
        tours_filtered = tour_df[tour_df['City'] == selected_city]
        flights_filtered_df = flight_df[flight_df['destination'] == selected_city]
        flights_filtered = Flight.objects.filter(destination=selected_city)

        selected_hotels = request.POST.getlist('hotels')
        selected_tours = request.POST.getlist('tours')
        selected_airlines = request.POST.getlist('airlines')

        hotel_recs = []
        tour_recs = []
        flight_recs = []

        # Xóa phần xử lý selected_flight_id vì không cần

        # Xử lý gợi ý dựa trên lựa chọn
        if selected_hotels or selected_tours or selected_airlines:
            # Gợi ý khách sạn
            if selected_hotels and not hotels_filtered.empty and len(hotels_filtered) > 1:
                hotel_sim = build_similarity_matrix(
                    hotel_df,
                    id_field='hotel_id',
                    categorical_features=['hotel_city', ],
                    numeric_features=['star_number', 'price', 'score_hotels', 'number_rating']
                )
                hotel_ids = recommend_items(selected_hotels, hotel_sim)
                hotel_recs = Hotel.objects.filter(hotel_id__in=hotel_ids).values()

            # Gợi ý tour
            if selected_tours and not tours_filtered.empty and len(tours_filtered) > 1:
                tour_sim = build_similarity_matrix(
                    tour_df,
                    id_field='tour_id',
                    categorical_features=['City'],
                    numeric_features=['price', 'duration', 'rating']
                )
                tour_ids = recommend_items(selected_tours, tour_sim)
                tour_recs = Tour.objects.filter(tour_id__in=tour_ids).values()

            # Gợi ý chuyến bay dựa trên hãng hàng không được chọn
            if selected_airlines:
                flight_recs = Flight.objects.filter(
                    destination=selected_city,
                    Airline__in=selected_airlines
                ).order_by('Price')[:5].values()

        hotels_full = Hotel.objects.filter(hotel_city=selected_city).values()
        tours_full = Tour.objects.filter(City=selected_city).values()
        flights_full = flights_filtered.values()

        context.update({
            'selected_city': selected_city,
            'hotels': list(hotels_full),
            'tours': list(tours_full),
            'flights': list(flights_full),
            'selected_hotels': selected_hotels,
            'selected_tours': selected_tours,
            'selected_airlines': selected_airlines,
            'recommended_hotels': list(hotel_recs),
            'recommended_tours': list(tour_recs),
            'recommended_flights': list(flight_recs),
        })

    return render(request, 'travel_recommend.html', context)