from abc import ABC
from enum import Enum

BOOKING_PREFIX = "KLM"


class AccountStatus(Enum):
    ACTIVE, INACTIVE, CANCELED, BLACKLISTED, BLOCKED = 1, 2, 3, 4, 5, 6


class Account:
    def __init__(self, password, status=AccountStatus.Active):
        self.__id = generate_id()
        self.__password = password
        self.__status = status

    def get_id(self):
        return self.__id


class Person(ABC):
    def __init__(self, first_name, last_name, age, mailing_address, residence_address):
        self.__first_name = first_name
        self.__last_name = last_name
        self.__age = age
        self.__mailing_address = mailing_address
        self.__residence_address = residence_address


class Customer(Person, Account):
    def __init__(self, first_name, last_name, email, phone, account):
        super.__init__(first_name, last_name, None, None)
        self.__email = email
        self.__phone = phone
        self.__account = account
        self.__bookings = []

    def get_bookings(self):
        return self.__bookings

    def add_booking(self, booking_id):
        self.__bookings.append(booking_id)


def generate_id():
    pass


class Booking:
    def __init__(self, customer, co_passengers, flight, itinerary, departure_time):
        """

        :param customer: Type Customer
        :param co_passengers: Type Person []
        :param flight: Type Flight
        :param itinerary: Type ItineraryHop []
        """
        self.id = BOOKING_PREFIX + generate_id()
        self.__customer = customer
        self.__co_passengers = co_passengers
        self.__flight = flight
        self.__itinerary = itinerary
        self.__departure_time = departure_time

    def get_booking_details(self):
        pass


class ItineraryHop:
    def __init__(self, hop, arrival_time, departure_time):
        self.hop_code = hop
        self.arrival_time = arrival_time
        self.departure_time = departure_time


class Passenger(Person):
    def __init__(self, passport_number, date_of_birth):
        self.__passport_number = passport_number
        self.__date_of_birth = date_of_birth

    def get_passport_number(self):
        return self.__passport_number


class Airport:
    def __init__(self, name, address, code):
        self.__name = name
        self.__address = address
        self.__code = code
        self.__originating_flights = []
        self.__layover_flights = []
        self.__terminating_flights = []

    def get_originating_flights(self):
        return self.__originating_flights

    def get_terminating_flights(self):
        return self.__terminating_flights

    def get_layover_flights(self):
        return self.__layover_flights

    def get_code(self):
        return self.__code

    def add_originating_flights(self, flight_number):
        self.__originating_flights.append(flight_number)

    def add_layover_flights(self, flight_number):
        self.__layover_flights.append(flight_number)

    def add_terminating_flights(self, flight_number):
        self.__terminating_flights.append(flight_number)


class Flight:
    def __init__(self, flight_number, route_hops):
        self.flight_number = flight_number
        self.route = route_hops
        self.flight_instances = dict()

    def get_hop(self, hop_code):
        return self.route[hop_code]

    def get_hop_next(self, hop_code):
        next_hop_code = self.route[hop_code].get("next")
        return self.route.get(next_hop_code)

    def validate_flight_availability(self, departure_time, number_of_seats, source, destination):
        # validate all the details
        return True


class FlightBookingService:
    def __init__(self, airports, flights, users):
        self.airports = dict()
        self.flights = dict()
        self.users = dict()
        self.bookings = dict()

        for airport in airports:
            self.airports[airport["code"]] = Airport(airport["name"], airport["address"], airport["code"])

        for flight in flights:
            hops = dict()
            source = flight["source"]
            hop = ItineraryHop(source["iata"], source["arrivalTime"], source["departureTime"])
            hops[source["iata"]] = {"current": hop, "next": source["destination"]["iata"]}
            self.airports[source["iata"]].add_originating_flights(flight["flightNumber"])

            while "destination" in source["destination"].keys():
                source = source["destination"]
                hop = ItineraryHop(source["iata"], source["arrivalTime"], source["departureTime"])
                hops[source["iata"]] = {"current": hop, "next": source["destination"]["iata"]}
                self.airports[source["iata"]].add_layover_flights(flight["flightNumber"])

            hop = ItineraryHop(source["iata"], source["arrivalTime"], None)
            hops[source["iata"]] = {"current": hop, "next": None}
            self.airports[source["iata"]].add_terminating_flights(flight["flightNumber"])
            self.flights[flight["flightNumber"]] = Flight(flight["flightNumber"], hops)

        for user in users:
            self.users[user["email"]] = Customer(user["firstName"], user["lastName"], user["emailId"], None, None)

    def search_booking(self, source, destination, departure_time):
        flights_from_src = self.airports[source].get_originating_flights()
        flights_to_dst = self.airports[destination].get_terminating_flights()
        flights_layover_dst = self.airports[destination].get_layover_flights()
        flights_layover_src = self.airports[source].get_layover_flights()

        flights_list = set(flights_from_src) & set(flights_layover_dst)
        flights_list += set(flights_layover_src) & set(flights_to_dst)
        flights_list += set(flights_layover_src) & set(flights_layover_dst)

        return [self._generate_flight_details(i, source, destination) for i in flights_list
                if self._filter_by_departure_time(source, i, departure_time)]

    def add_booking(self, flight_number, source, destination, passengers, departure_time):
        self._validate_booking_input(flight_number, source, destination, departure_time, len(passengers))

        primary_passenger = passengers[0]
        customer = self.users[primary_passenger["emailId"]]
        flight = self.flights[flight_number]
        flight.flight_instances[departure_time]["seats"] -= len(passengers)

        passengers_list = []
        for passenger in passengers[1:]:
            pax = Person(passenger["firstName"], passenger["lastName"], passenger["age"], None, None)
            passengers_list.append(pax)

        booking = Booking(customer, passengers_list, flight, departure_time,
                          self._generate_flight_details(flight_number, source, destination)["itinerary"])
        self.bookings[booking.id] = booking
        customer.add_booking(booking.id)

    def _validate_booking_input(self, flight_number, source, destination, departure_time, number_of_seats):
        pass

    def _filter_by_departure_time(self, s, i, t):
        return self.flights[i].route[s]["current"].departure_time >= t

    def _generate_flight_details(self, flight_num, source, destination):
        hop_count = 0
        hop = self.flights[flight_num].route[source]
        route = hop["current"].hop_code
        departure_time = hop["current"].departure_time

        while hop["current"].hop_code != destination:
            hop = self.flights[flight_num].route[hop["next"]]
            route += "->" + hop["current"].hop_code
            hop_count += 1

        arrival_time = hop["current"].arrival_time

        return {"flightNumber": flight_num,
                "departureTime": departure_time,
                "arrivalTime": arrival_time,
                "itinerary": route,
                "hops": hop_count}

