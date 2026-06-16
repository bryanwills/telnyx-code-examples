FROM ruby:3.3-slim

WORKDIR /app

COPY Gemfile Gemfile.lock* ./
RUN bundle install

COPY . .

EXPOSE 3000

CMD ["ruby", "app.rb"]
